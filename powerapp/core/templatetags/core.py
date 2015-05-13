# -*- coding: utf-8 -*-
import json
import collections
from django import template
from django.contrib.messages.storage.base import Message
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter('to_json')
def to_json(value):
    return mark_safe(json.dumps(value, separators=',:', default=json_default))


def json_default(value):
    if isinstance(value, collections.Iterable):
        return list(value)
    if isinstance(value, Message):
        return value.__dict__
    raise TypeError('%r is not JSON serializable' % value)
