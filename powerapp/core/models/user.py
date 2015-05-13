import logging
import datetime

from django.utils.functional import cached_property
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils.timezone import now
from django.conf import settings

from picklefield.fields import PickledObjectField
from powerapp.core.sync import TodoistAPI


EMPTY_SCOPE = '__all__'
SYNC_PERIOD = datetime.timedelta(minutes=1 if settings.DEBUG else 30)


logger = logging.getLogger(__name__)


class User(AbstractBaseUser):

    USERNAME_FIELD = 'email'

    # Main user fields
    id = models.IntegerField(primary_key=True)
    email = models.CharField(db_index=True, unique=True, max_length=255)

    # API client fields
    api_state = PickledObjectField()
    api_token = models.CharField(db_index=True, max_length=255)
    api_last_sync = models.DateTimeField(db_index=True)
    api_next_sync = models.DateTimeField(db_index=True)

    class Meta:
        app_label = 'core'

    def __str__(self):
        return self.email

    def save(self, **kwargs):
        # move next_sync forward
        threshold = self.api_last_sync or now()
        if not self.api_next_sync or self.api_next_sync < threshold:
            self.api_next_sync = threshold + SYNC_PERIOD
        super(User, self).save(**kwargs)


    @classmethod
    def register(cls, token):
        """
        Register new user by access token.

        We don't re-register a user if it's already stored,  but return a
        previously stored user instead.
        """
        obj = cls(api_token=token)
        obj.api.user.sync()
        return obj

    def reset_api(self):
        self.api_state = None
        self.api_last_sync = None
        self.api_next_sync = None
        self.api = TodoistAPI.create(self)
        self.api.user.sync()

    @cached_property
    def api(self):
        return TodoistAPI.create(self)
