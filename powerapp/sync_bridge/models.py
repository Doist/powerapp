# -*- coding: utf-8 -*-
import json
from django.db import models
from django.utils.text import Truncator
from picklefield.fields import PickledObjectField


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
    left_extra = PickledObjectField(u'Extra data of the "left side"', default={})

    right_id = models.CharField(u'"Right system" item id', max_length=512, null=True, db_index=True)
    right_hash = models.CharField(u'Last seen hash of the item', max_length=64, default='!')
    right_extra = PickledObjectField(u'Extra data of the "right side"', default={})

    class Meta:
        index_together = [
            ['integration', 'bridge_name', 'left_id'],
            ['integration', 'bridge_name', 'right_id'],
        ]

    def __log__(self):
        """
        Logging utils use this information to convert object to a log record
        """
        return {
            'id': self.id,
            'integration_id': self.integration_id,
            'bridge_name': self.bridge_name,
            'left_id': self.left_id,
            'left_hash': hash_and_extra(self.left_hash, self.left_extra),
            'right_id': self.right_id,
            'right_hash': hash_and_extra(self.right_hash, self.right_extra),
        }

    def __str__(self):
        return '%s: %s (%s) -> %s (%s)' % (self.bridge_name,
                                           self.left_id,
                                           hash_and_extra(self.left_hash, self.left_extra),
                                           self.right_id,
                                           hash_and_extra(self.right_hash, self.right_extra))


def hash_and_extra(hash_value, extra_value):
    ret = hash_value[:6]
    if extra_value:
        shorten_extra = {}
        for k, v in extra_value.items():
            shorten_extra[Truncator(k).chars(20)] = Truncator(v).chars(20)
        ret += ' %s' % json.dumps(shorten_extra)
    return ret
