# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings
from picklefield import PickledObjectField


class Integration(models.Model):

    name = models.CharField(max_length=1024)
    service = models.ForeignKey('Service', max_length=1024)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    next_sync = models.IntegerField(db_index=True, default=0)
    settings = PickledObjectField(default={})

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'core'
        index_together = ['user', 'service']

    def update_settings(self, **kwargs):
        self.settings = dict(self.settings or {}, **kwargs)
        self.save()
