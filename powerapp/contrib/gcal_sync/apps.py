# -*- coding: utf-8 -*-
"""
Synchronizes your Todoist tasks with your Google Calendar
"""
import environ
from powerapp.core.apps import ServiceAppConfig


env = environ.Env()


class AppConfig(ServiceAppConfig):
    name = 'powerapp.contrib.gcal_sync'
    verbose_name = 'Google Calendar Sync'
    url = 'https://calendar.google.com'
    description = __doc__

    GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default=None)
    GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET', default=None)
