# -*- coding: utf-8 -*-
from django.db import models



class BridgeManager(models.Manager):

    def bridge_delete(self, bridge, **kwargs):
        return self.get_queryset().filter(integration=bridge.integration,
                                          bridge_name=bridge.name, **kwargs).delete()

    def bridge_create(self, bridge, **kwargs):
        return self.get_queryset().create(integration=bridge.integration,
                                          bridge_name=bridge.name, **kwargs)

    def bridge_filter(self, bridge, **kwargs):
        return self.get_queryset().filter(integration=bridge.integration,
                                          bridge_name=bridge.name, **kwargs)

    def bridge_get(self, bridge, **kwargs):
        return self.get_queryset().get(integration=bridge.integration,
                                       bridge_name=bridge.name, **kwargs)



class ItemMapping(models.Model):

    objects = BridgeManager()

    # a part of the compound key to identify the bridge
    integration = models.ForeignKey('core.Integration')
    bridge_name = models.CharField(max_length=512)

    # item requisites
    left_id = models.CharField(u'"Left system" item id', max_length=512, null=True, db_index=True)
    left_hash = models.CharField(u'Last seen hash of the item', max_length=64, default='!')

    right_id = models.CharField(u'"Right system" item id', max_length=512, null=True, db_index=True)
    right_hash = models.CharField(u'Last seen hash of the item', max_length=64, default='!')

    class Meta:
        index_together = [
            ['integration', 'bridge_name', 'left_id'],
            ['integration', 'bridge_name', 'right_id'],
        ]
