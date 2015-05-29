# -*- coding: utf-8 -*-
import datetime
from logging import getLogger
from django.dispatch.dispatcher import receiver
from .apps import AppConfig
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from powerapp.contrib.evernote_sync.sync_adapter import EvernoteSyncAdapter
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



@AppConfig.periodic_task(datetime.timedelta(minutes=1))
def minute_counter(integration, user):
    # TODO: polling and sync

    # See
    # https://dev.evernote.com/doc/articles/search.php
    # https://dev.evernote.com/doc/articles/polling_notification.php
    # https://dev.evernote.com/doc/articles/search_grammar.php
    # https://dev.evernote.com/doc/reference/NoteStore.html#Fn_NoteStore_findNotesMetadata
    filt = NoteFilter(words="any: created:20150529T100000 updated:20150529T100000")
    spec = NotesMetadataResultSpec()
    client = utils.get_evernote_client(user)
    store = client.get_note_store()
    metadata = store.findNotesMetadata(filt, 0, 100, spec)
    # ...
