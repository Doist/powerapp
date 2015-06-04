# -*- coding: utf-8 -*-
from django.db.models.signals import post_save
from django.dispatch import receiver

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
