# -*- coding: utf-8 -*-
import datetime
from logging import getLogger
from django.conf import settings
from django.dispatch.dispatcher import receiver
from .apps import AppConfig
from powerapp.contrib.evernote_sync.sync_adapter import EvernoteSyncAdapter, \
    get_bridge_by_guid, task_from_evernote, build_bridge
from powerapp.sync_bridge.bridge import SyncBridge
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter, \
    task_from_todoist
from . import utils


logger = getLogger(__name__)


@receiver(AppConfig.signals.todoist_task_added)
@receiver(AppConfig.signals.todoist_task_updated)
def on_task_changed(sender, user=None, service=None, integration=None, obj=None, **kwargs):
    # let's see if we have to keep track of this
    guid = integration.settings.get('projects_notebooks', {}).get(obj['project_id'])
    if guid is None:
        return

    td = TodoistSyncAdapter(obj['project_id'])
    ev = EvernoteSyncAdapter(guid)
    bridge = SyncBridge(integration, td, ev)
    bridge.push_task(td, obj['id'], task_from_todoist(obj))


@receiver(AppConfig.signals.todoist_task_deleted)
def on_task_deleted(sender, user=None, service=None, integration=None, obj=None, **kwargs):
    # let's see if we have to keep track of this
    guid = integration.settings.get('projects_notebooks', {}).get(obj['project_id'])
    if guid is None:
        return

    td = TodoistSyncAdapter(obj['project_id'])
    ev = EvernoteSyncAdapter(guid)
    bridge = SyncBridge(integration, td, ev)
    bridge.delete_task(td, obj['id'])


@receiver(utils.evernote_note_changed)
def on_note_changed(sender, integration, note, **kwargs):
    if note.notebookGuid not in integration.settings.get('evernote_notebooks', []):
        return

    task = task_from_evernote(integration.user, note)
    if task is None:
        return

    projects_notebooks = integration.settings.get('projects_notebooks') or {}
    notebooks_projects = {v: k for k, v in projects_notebooks.items()}
    project_id = notebooks_projects.get(note.notebookGuid)
    bridge = build_bridge(integration, project_id, note.notebookGuid)
    bridge.push_task(bridge.right, note.guid, task)


@receiver(utils.evernote_note_deleted)
def on_note_deleted(sender, integration, guid, **kwargs):
    bridge = get_bridge_by_guid(integration, guid)
    if bridge:
        bridge.delete_task(bridge.right, guid)


@AppConfig.periodic_task(datetime.timedelta(minutes=1 if settings.DEBUG else 15))
def sync_evernote(integration):
    utils.sync_evernote(integration)
