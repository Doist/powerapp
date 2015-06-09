# -*- coding: utf-8 -*-
"""
Synchronizes your Todoist tasks with your Evernote reminders
"""
import environ
from powerapp.core.apps import ServiceAppConfig


env = environ.Env()


class AppConfig(ServiceAppConfig):
    name = 'powerapp.contrib.evernote_sync'
    verbose_name = 'Evernote Sync'
    url = 'https://evernote.com'
    description = __doc__

    EVERNOTE_CONSUMER_KEY = env('EVERNOTE_CONSUMER_KEY', default=None)
    EVERNOTE_CONSUMER_SECRET = env('EVERNOTE_CONSUMER_SECRET', default=None)
    EVERNOTE_SANDBOX = env.bool('EVERNOTE_SANDBOX', default=True)
    EVERNOTE_USE_POLLING = env.bool('EVERNOTE_USE_POLLING', default=False)
    EVERNOTE_WEBHOOK_SECRET_KEY = env('EVERNOTE_WEBHOOK_SECRET_KEY', default=None)
