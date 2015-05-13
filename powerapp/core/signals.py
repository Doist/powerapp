# -*- coding: utf-8 -*-
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Integration
from . import periodic_tasks


@receiver(post_save, sender=Integration)
def on_integration_create(sender, instance=None, created=None, **kwargs):
    if created:
        periodic_tasks.add(instance)
