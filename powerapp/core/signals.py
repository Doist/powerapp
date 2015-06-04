# -*- coding: utf-8 -*-
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from django_statsd.clients import statsd

from .models import Integration, Service
from . import periodic_tasks


@receiver(post_save, sender=Integration)
def on_integration_create(sender, instance=None, created=None, **kwargs):
    if created:
        # create periodic tasks
        periodic_tasks.add(instance)


@receiver(post_save, sender=Service)
def change_enabled_status_on_service_update(sender, instance=None, created=None, **kwargs):
    Integration.objects.filter(service=instance).update(service_enabled=instance.enabled)


@receiver(post_save, sender=Integration)
def integration_cnt_incr(sender, instance=None, created=None, **kwargs):
    if created:
        statsd.incr('integration_cnt')
        statsd.incr('integration_cnt.%s' % instance.service_id)


@receiver(post_delete, sender=Integration)
def integration_cnt_decr(sender, instance=None, **kwargs):
    statsd.decr('integration_cnt')
    statsd.decr('integration_cnt.%s' % instance.service_id)
