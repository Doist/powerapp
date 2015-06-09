# -*- coding: utf-8 -*-
import datetime
from logging import getLogger
from django.conf import settings
from django.dispatch.dispatcher import receiver
from .apps import AppConfig
from powerapp.contrib.evernote_sync.sync_adapter import EvernoteSyncAdapter, \
    get_bridge_by_guid, build_bridge
from powerapp.core.exceptions import PowerAppInvalidTokenError
from powerapp.sync_bridge.bridge import SyncBridge
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter
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
    bridge.push_task(td, obj['id'], obj)


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
    # we don't care about this note
    if note.notebookGuid not in integration.settings.get('evernote_notebooks', []):
        return
    # this note doesn't have a reminder, skip it as well
    if not note.attributes.reminderOrder:
        return
    projects_notebooks = integration.settings.get('projects_notebooks') or {}
    notebooks_projects = {v: k for k, v in projects_notebooks.items()}
    project_id = notebooks_projects.get(note.notebookGuid)
    bridge = build_bridge(integration, project_id, note.notebookGuid)
    bridge.push_task(bridge.right, note.guid, note)


@receiver(utils.evernote_note_deleted)
def on_note_deleted(sender, integration, guid, **kwargs):
    bridge = get_bridge_by_guid(integration, guid)
    if bridge:
        bridge.delete_task(bridge.right, guid)


if settings.EVERNOTE_USE_POLLING:
    @AppConfig.periodic_task(datetime.timedelta(minutes=1 if settings.DEBUG else 15))
    def sync_evernote(integration):
        try:
            utils.sync_evernote(integration)
        except PowerAppInvalidTokenError:
            logger.warning("Evernote access token for %s not found. "
                           "Skip synchronization", integration.user)
