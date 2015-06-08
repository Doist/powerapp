# -*- coding: utf-8 -*-
from logging import getLogger
from django.dispatch.dispatcher import receiver
from .apps import AppConfig
from powerapp.contrib.gcal_sync.sync_adapter import GcalSyncAdapter
from powerapp.sync_bridge.bridge import SyncBridge, task
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter
from . import utils, sync_adapter


logger = getLogger(__name__)


@receiver(AppConfig.signals.todoist_task_added)
@receiver(AppConfig.signals.todoist_task_updated)
def on_task_changed(sender, integration=None, obj=None, **kwargs):
    td = TodoistSyncAdapter(obj['project_id'])
    gc = GcalSyncAdapter()
    bridge = SyncBridge(integration, td, gc)

    # we delete tasks, if they're marked as "in history"
    if obj['in_history']:
        bridge.delete_task(td, obj['id'])
    else:
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
    # we don't delete task, but instead we mark the task as "checked"
    bridge.push_task(bridge.right, event_id, task(checked=True, in_history=True))
