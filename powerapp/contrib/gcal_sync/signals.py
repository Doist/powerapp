# -*- coding: utf-8 -*-
import datetime
from logging import getLogger
from django.conf import settings
from django.dispatch.dispatcher import receiver
from .apps import AppConfig
from powerapp.contrib.gcal_sync.sync_adapter import GcalSyncAdapter
from powerapp.sync_bridge.bridge import SyncBridge
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter
from . import utils


logger = getLogger(__name__)


@receiver(AppConfig.signals.todoist_task_added)
@receiver(AppConfig.signals.todoist_task_updated)
def on_task_changed(sender, user=None, service=None, integration=None, obj=None, **kwargs):
    td = TodoistSyncAdapter(obj['project_id'])
    gc = GcalSyncAdapter()
    bridge = SyncBridge(integration, td, gc)
    bridge.push_task(td, obj['id'], obj)


@receiver(AppConfig.signals.todoist_task_deleted)
def on_task_deleted(sender, user=None, service=None, integration=None, obj=None, **kwargs):
    td = TodoistSyncAdapter(obj['project_id'])
    gc = GcalSyncAdapter()
    bridge = SyncBridge(integration, td, gc)
    bridge.delete_task(td, obj['id'])


@AppConfig.periodic_task(datetime.timedelta(minutes=1 if settings.DEBUG else 15))
def sync_gcal(integration):
    utils.sync_gcal(integration)
