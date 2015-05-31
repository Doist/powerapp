# -*- coding: utf-8 -*-
import re
import time
from evernote.edam.error.ttypes import EDAMNotFoundException
import evernote.edam.type.ttypes as Types
from powerapp.sync_bridge.bridge import SyncAdapter, SyncBridge, task
from powerapp.sync_bridge.models import ItemMapping
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter
from . import utils


REMINDER_BASE_TIME = 946684800   # millenium


def build_bridge(integration, project_id, notebook_guid):
    td = TodoistSyncAdapter(project_id)
    ev = EvernoteSyncAdapter(notebook_guid)
    return SyncBridge(integration, td, ev)


def get_bridge_by_guid(integration, guid):
    """
    Return SyncBridge instance (or None) by task GUID

    We need this function, because there is no way to identify the notebook
    guid by item id, and so we're forced to use this dirty workaround

    Note that here we rely on the fact that the bridge has a predictable
    structure (todoist <--> evernote) and sides of the bridge have predictable
    names containing id of the project and the guid of the notebook coresondingly
    """
    try:
        mapping = ItemMapping.objects.get(right_id=guid, integration=integration)
    except ItemMapping.DoesNotExist:
        return None
    match = re.compile(r'^todoist-(\d+)-evernote-(.*)$').match(mapping.bridge_name)
    if not match:
        return None

    return build_bridge(integration, match.group(1), match.group(2))


class EvernoteSyncAdapter(SyncAdapter):
    """
    Sync Adapter for Todoist. Used to sync data between the chosen project in
    Todoist, and a third-party library.

    Does not support syncing of tags yet
    """
    DEFAULT_NAME = 'evernote'
    ESSENTIAL_FIELDS = ['content', 'item_order', 'checked']

    def __init__(self, notebook_guid):
        name = '%s-%s' % (self.DEFAULT_NAME, notebook_guid)
        super(EvernoteSyncAdapter, self).__init__(name=name)
        self.notebook_guid = notebook_guid

    def push_task(self, task_id, task):
        client = utils.get_evernote_client(self.user)
        note_store = client.get_note_store()

        if task_id:
            try:
                note = note_store.getNote(task_id, True, True, False, False)
                create = False
            except EDAMNotFoundException:
                note = Types.Note()
                create = True
        else:
            note = Types.Note()
            create = True

        note.title = plaintext_content(task.content)
        if create:
            note.content = utils.format_note_content('')
        note.notebookGuid = self.notebook_guid

        note.attributes = Types.NoteAttributes()
        note.attributes.reminderOrder = REMINDER_BASE_TIME - task.item_order
        if task.checked:
            note.attributes.reminderDoneTime = int(time.time())
        else:
            note.attributes.reminderDoneTime = None

        if create:
            note = note_store.createNote(note)
        else:
            note = note_store.updateNote(note)

        return note.guid

    def delete_task(self, task_id):
        client = utils.get_evernote_client(self.user)
        note_store = client.get_note_store()
        try:
            note_store.deleteNote(task_id)
        except EDAMNotFoundException:
            pass


def task_from_evernote(user, note):
    """
    Take an evernote Note and return a new generic task.

    If evernote note doesn't have to be synchronized with Todoist, return
    None
    """
    if not note.attributes.reminderOrder:
        return None

    note_url = utils.get_note_url(user, note.guid)
    content = '%s (%s)' % (note_url, note.title)

    item_order = REMINDER_BASE_TIME - note.attributes.reminderOrder
    if item_order < 1:
        item_order = 1
    return task(checked=note.attributes.reminderDoneTime is not None,
                content=content, item_order=item_order)

def plaintext_content(content):
    """
    Get rid of note_url (it's added by `task_from_evernote`) and keep just the
    plain content of the note
    """
    match = re.compile(r'^https?://\S*evernote.com.*?\((.*)\)$').match(content)
    if match:
        return match.group(1)
    else:
        return content
