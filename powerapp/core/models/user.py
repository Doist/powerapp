import re
import pytz
import datetime
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.timezone import now, make_aware
from picklefield.fields import PickledObjectField
from todoist.api import TodoistAPI
from powerapp.core.sync import UserTodoistAPI

SYNC_PERIOD = datetime.timedelta(minutes=1 if settings.DEBUG else 30)


class UserManager(models.Manager):

    def register(self, api_token):
        """ Register a new user """
        try:
            return self.get(api_token=api_token)
        except ObjectDoesNotExist:
            # Use "classic API", we don't need connection to any model
            api = TodoistAPI(api_token, api_endpoint=settings.API_ENDPOINT)
            api.user.sync()
            # At this point we have a locally stored user data, including API
            # or token. Create a new user, or update existing one
            data = {'email': api.user.get('email'), 'api_token': api_token}
            obj, _ = self.update_or_create(id=api.user.get('id'),
                                           defaults=data)
            return obj


class User(AbstractBaseUser):

    # Woohoo! Millenium!
    MILLENIUM = make_aware(datetime.datetime(2000, 1, 1))

    USERNAME_FIELD = 'id'
    objects = UserManager()

    id = models.IntegerField(primary_key=True)
    # note: although both email and api token are supposed to be unique, we
    # don't require the database uniqueness for them, because in some corner
    # cases, because the local database isn't always fully in sync with the
    # upstream, we may end up with twi users having the same email.
    email = models.CharField(db_index=True, max_length=255)
    api_token = models.CharField(db_index=True, max_length=255)

    # we use these data exclusively to keep track of user personal data
    api_state = PickledObjectField()
    api_last_sync = models.DateTimeField(default=MILLENIUM, db_index=True)

    @cached_property
    def api(self):
        """
        The API object which should be used exclusively for getting user
        personal data, such as email, full name, avatar, etc, but not tasks or
        projects.

        For tasks and items most likely you should use integration-attached
        API objects
        """
        obj = UserTodoistAPI.create(self)
        if self.api_last_sync < now() - SYNC_PERIOD:
            obj.sync(resource_types=["projects", "labels", "filters"])
            obj.user.sync()
        return obj

    def reset_api(self):
        self.api_state = ''
        self.api_last_sync = self.MILLENIUM
        self.save()

    def get_timezone(self):
        """
        Return pytz timezone object from User settings
        """
        tzname = self.api.user.get('timezone')
        if tzname is None:
            self.api.user.sync()
            tzname = self.api.user.get('timezone')
            if not tzname:
                tzname = 'UTC'

        pytz_tzname = tzname_todoist_to_pytz(tzname)
        return pytz.timezone(pytz_tzname)

    def get_inbox_project(self):
        return self.api.user.get('inbox_project')

    class Meta:
        app_label = 'core'

    def __str__(self):
        return self.email

    def __log__(self):
        return {
            'id': self.id,
            'email': self.email,
        }



re_todoist_static_tz = re.compile(r'GMT ([+-])(\d+):00$')


def tzname_todoist_to_pytz(timezone_name):
    """
    GMT +XX:00 has to be converted to Etc/GMT-XX (mind that we change + to -
    and vice versa)
    """
    match = re_todoist_static_tz.match(timezone_name)
    if match:
        plus_minus = match.group(1)
        sign = {'+': '-', '-': '+'}[plus_minus]
        return 'Etc/GMT%s%s' % (sign, match.group(2))
    else:
        return timezone_name
