# -*- coding: utf-8 -*-
import datetime
from logging import getLogger
from django.conf import settings
from django.dispatch.dispatcher import receiver
from .apps import AppConfig
from powerapp.contrib.gcal_sync.sync_adapter import GcalSyncAdapter
from powerapp.sync_bridge.bridge import SyncBridge
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter
from . import utils, sync_adapter


logger = getLogger(__name__)


@receiver(AppConfig.signals.todoist_task_added)
@receiver(AppConfig.signals.todoist_task_updated)
def on_task_changed(sender, integration=None, obj=None, **kwargs):
    td = TodoistSyncAdapter(obj['project_id'])
    gc = GcalSyncAdapter()
    bridge = SyncBridge(integration, td, gc)
    bridge.push_task(td, obj['id'], obj)


@receiver(AppConfig.signals.todoist_task_deleted)
def on_task_deleted(sender, integration=None, obj=None, **kwargs):
    td = TodoistSyncAdapter(obj['project_id'])
    gc = GcalSyncAdapter()
    bridge = SyncBridge(integration, td, gc)
    bridge.delete_task(td, obj['id'])


@receiver(utils.gcal_event_changed)
def on_gcal_event_changed(sender, integration=None, event=None, **kwargs):
    bridge = sync_adapter.get_bridge_by_event_id(integration, event['id'])
    bridge.push_task(bridge.right, event['id'], event)


@receiver(utils.gcal_event_deleted)
def on_gcal_event_deleted(sender, integration=None, event_id=None, **kwargs):
    bridge = sync_adapter.get_bridge_by_event_id(integration, event_id)
    bridge.delete_task(bridge.right, event_id)


@AppConfig.periodic_task(datetime.timedelta(minutes=1 if settings.DEBUG else 60))
def sync_gcal(integration):
    """
    Sync our Google Calendar tasks periodically in case webhooks don't work
    """
    utils.sync_gcal(integration)
