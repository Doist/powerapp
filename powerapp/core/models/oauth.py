import logging

from django.db import models
from django.conf import settings


logger = logging.getLogger(__name__)


class AbstractOAuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    client = models.CharField('OAuth client name', max_length=128)
    token = models.CharField('OAuth token value', max_length=1024)
    time = models.DateTimeField('Time token added', auto_now_add=True)

    class Meta:
        app_label = 'core'
        abstract = True
        unique_together = [
            ('user', 'client', 'scope'),
        ]

    def __str__(self):
        return '%s:%s' % (self.client, self.scope)

    @classmethod
    def register(cls, user, client, token):
        """
        Register new access token.

        In addition, we don't keep duplicates, and we keep unique values for
        (user, client) tuples.
        """
        obj, _ = cls.objects.update_or_create(client=client, user=user,
                                              defaults={'token': token})
        return


class AccessToken(AbstractOAuthToken):
    class Meta:
        app_label = 'core'
