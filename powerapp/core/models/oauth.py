import datetime
import logging

from django.db import models
from django.conf import settings
from django.utils.timezone import now

from powerapp.core.attrdict import AttrDict


EMPTY_SCOPE = '__all__'
logger = logging.getLogger(__name__)


class TodoistEvent(AttrDict):
    pass


class AbstractOAuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    client = models.CharField('OAuth client name', max_length=128)
    scope = models.CharField('OAuth scope', max_length=1024)
    token = models.CharField('OAuth token value', max_length=1024)
    time = models.DateTimeField('Time token added', auto_now_add=True)

    class Meta:
        app_label = 'core'
        abstract = True
        unique_together = [
            ('user', 'client', 'scope'),
        ]

    @classmethod
    def register(cls, user, client, scope, token):
        """
        Register new access token. We accept the `scope` as comma-separated
        list of values, split it, and store every scope item as a separate
        database record.

        In addition, we don't keep duplicates, and we keep unique values for
        (user, client, scope) tuples.

        If scope is empty (some OAuth servers don't use the concept of scope)
        we internally keep the scope under the "__all__" name.
        """
        if scope is None:
            scope = 'all'

        ret = []
        scope = scope.strip() or EMPTY_SCOPE
        for sc in scope.split(','):
            obj, _ = cls.objects.update_or_create(client=client, user=user,
                                                  scope=sc,
                                                  defaults={'token': token})
            ret.append(obj)
        return ret


class AccessToken(AbstractOAuthToken):
    class Meta:
        app_label = 'core'


class RefreshToken(AbstractOAuthToken):
    class Meta:
        app_label = 'core'


def cron_sync(sync_interval=300):
    """
    Find all users who weren't recently updated, and update them all,
    one by one.

    :param check_interval: the Sync interval (in seconds)
    """
    from powerapp.core.models import User
    # TODO: we might perform sync operations in parallel
    next_sync = now() + datetime.timedelta(seconds=sync_interval)
    for user in User.objects.filter(next_sync__lte=now):
        user.cron_sync()
        user.next_sync = next_sync
        user.save()
