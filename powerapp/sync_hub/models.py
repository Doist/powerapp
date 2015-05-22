# -*- coding: utf-8 -*-
from django.db import models



class HubManager(models.Manager):

    def hub_delete(self, hub, **kwargs):
        return self.get_queryset().filter(integration=hub.integration,
                                          hub_name=hub.name, **kwargs).delete()

    def hub_create(self, hub, **kwargs):
        return self.get_queryset().create(integration=hub.integration,
                                          hub_name=hub.name, **kwargs)

    def hub_filter(self, hub, **kwargs):
        return self.get_queryset().filter(integration=hub.integration,
                                          hub_name=hub.name, **kwargs)

    def hub_get(self, hub, **kwargs):
        return self.get_queryset().get(integration=hub.integration,
                                       hub_name=hub.name, **kwargs)



class MetaItem(models.Model):

    objects = HubManager()

    integration = models.ForeignKey('core.Integration')
    hub_name = models.CharField(max_length=512)
    item_hash = models.CharField(max_length=64)

    class Meta:
        index_together = ['integration', 'hub_name']


class LocalItem(models.Model):

    objects = HubManager()

    integration = models.ForeignKey('core.Integration')
    hub_name = models.CharField(max_length=512)
    queue_name = models.CharField(max_length=512)
    local_id = models.CharField(max_length=512)
    meta_item = models.ForeignKey('MetaItem')
