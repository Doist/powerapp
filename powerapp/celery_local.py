# -*- coding: utf-8 -*-
from . import runner; runner.configure_app()

from celery import Celery
from django.conf import settings

app = Celery('powerapp')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
