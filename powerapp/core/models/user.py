import datetime
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.timezone import now
from picklefield.fields import PickledObjectField
from todoist.api import TodoistAPI


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
    api_last_sync = models.DateTimeField(db_index=True)

    @cached_property
    def api(self):
        """
        The API object which should be used exclusively for getting user
        personal data, such as email, full name, avatar, etc, but not tasks or
        projects.

        For tasks and items most likely you should use integration-attached
        API objects
        """
        if self.api_state:
            obj = TodoistAPI.deserialize(self.api_state)
        else:
            obj = TodoistAPI(self.api_token)
        obj.api_endpoint = settings.API_ENDPOINT

        if self.api_last_sync < now() - SYNC_PERIOD:
            obj.user.sync()
            self.api_last_sync = now()
            self.api_state = obj.serialize()

        return obj

    class Meta:
        app_label = 'core'

    def __str__(self):
        return self.email
