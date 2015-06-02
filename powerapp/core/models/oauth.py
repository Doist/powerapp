import logging
import datetime
from django.db import models
from django.conf import settings
from django.utils.timezone import now

# token, returned by most services, is a dict containing the access
# token at least, and may or may not contain some extra fields
#
# {
#   'token_type': 'Bearer',
#   'refresh_token': 'xxxxxxxxxxxxxxxxx',
#   'expires_in': 3600,
#   'access_token': 'xxxxxxxxxxxxxxxxx'
# }

logger = logging.getLogger(__name__)


class OAuthToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    client = models.CharField('OAuth client name', max_length=128)
    access_token = models.CharField('OAuth access token', max_length=1024)
    refresh_token = models.CharField('OAuth refresh token', max_length=1024, null=True)
    token_type = models.CharField('Token type', max_length=64, default='Bearer')
    access_token_expires = models.DateTimeField('Access token expiration date',
                                                null=True, default=None)

    class Meta:
        app_label = 'core'
        unique_together = [
            ('user', 'client'),
        ]

    def __str__(self):
        return '%s:%s' % (self.client, self.token_type)

    @classmethod
    def register(cls, user, client,
                 access_token, expires_in=None,
                 refresh_token=None,
                 token_type='Bearer'):
        """
        Register new access token.
        """
        if expires_in is not None:
            # we want to update the token at least one min before it expires
            access_token_expires = now() + datetime.timedelta(seconds=expires_in - 60)
        else:
            access_token_expires = None

        default_values = {
            'access_token': access_token,
            'access_token_expires': access_token_expires,
            'refresh_token': refresh_token,
            'token_type': token_type,
        }
        obj, _ = cls.objects.update_or_create(client=client, user=user,
                                              defaults=default_values)
        return obj

    def get_expires_in(self):
        if self.access_token_expires is None:
            return 3600  # always return some positive value
        return int((self.access_token_expires - now()).total_seconds())

    def refresh(self, token):
        self.access_token = token['access_token']
        self.access_token_expires = now() + datetime.timedelta(seconds=token['expires_in'] - 60)
        self.save()
