# -*- coding: utf-8 -*-
import time
from evernote.edam.error.ttypes import EDAMNotFoundException
import evernote.edam.type.ttypes as Types
from powerapp.sync_bridge.bridge import SyncAdapter, SyncBridge
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter
from . import utils


def build_bridge(integration, project_id, notebook_guid):
    td = TodoistSyncAdapter(project_id)
    ev = EvernoteSyncAdapter(notebook_guid)
    return SyncBridge(integration, td, ev)


REMINDER_BASE_TIME = 946684800   # millenium


class EvernoteSyncAdapter(SyncAdapter):
    """
    Sync Adapter for Todoist. Used to sync data between the chosen project in
    Todoist, and a third-party library.

    Does not support syncing of tags yet
    """
    DEFAULT_NAME = 'evernote'
    ESSENTIAL_FIELDS = ['content', 'item_order', 'checked']

    def __init__(self, notebook_guid, name=None):
        if name is None:
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

        note.title = task.content
        if create:
            note.content = utils.format_note_content('')
        note.notebookGuid = self.notebook_guid

        note.attributes = Types.NoteAttributes()
        note.attributes.reminderOrder = REMINDER_BASE_TIME - task.item_order
        if task.checked:
            note.attributes.reminderDoneTime = int(time.time())

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
