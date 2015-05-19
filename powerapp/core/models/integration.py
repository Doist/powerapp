# -*- coding: utf-8 -*-
import datetime
from django.db import models
from django.utils.timezone import now, make_aware
from django.conf import settings
from django.apps import apps
from django.utils.functional import cached_property
from picklefield import PickledObjectField
from powerapp.core.sync import TodoistAPI


SYNC_PERIOD = datetime.timedelta(minutes=1 if settings.DEBUG else 30)


class Integration(models.Model):

    # Woohoo! Millenium!
    MILLENIUM = make_aware(datetime.datetime(2000, 1, 1))

    name = models.CharField(max_length=1024)
    service = models.ForeignKey('Service', max_length=1024)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    next_sync = models.IntegerField(db_index=True, default=0)
    settings = PickledObjectField(default={})

    # API client fields
    stateless = models.BooleanField(default=True)
    api_state = PickledObjectField()
    api_last_sync = models.DateTimeField(default=MILLENIUM)
    api_next_sync = models.DateTimeField(default=MILLENIUM)

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'core'
        index_together = [
            ['user', 'service'],
            ['stateless', 'api_next_sync']
        ]

    def update_settings(self, **kwargs):
        self.settings = dict(self.settings or {}, **kwargs)
        self.save(update_fields=['settings'])

    def reset_api(self):
        if not self.stateless:
            self.api_state = None
            self.api_last_sync = self.MILLENIUM
            self.api_next_sync = self.MILLENIUM
            self.api = TodoistAPI.create(self)
            self.api.user.sync()

    @cached_property
    def api(self):
        return TodoistAPI.create(self)

    @property
    def app_config(self):
        """
        Return the initialized Application Config instance, connected to
        this instance's service. It's here to avoid extra database query
        for requests like `instance.service.app_config`

        :rtype: powerapp.core.apps.ServiceAppConfig
        """
        return apps.get_app_config(self.service_id)

    def save(self, **kwargs):
        # move next_sync forward if needed
        threshold = self.api_last_sync or now()
        if not self.stateless and (not self.api_next_sync
                                   or self.api_next_sync < threshold):
            self.api_next_sync = threshold + SYNC_PERIOD
        super(Integration, self).save(**kwargs)
