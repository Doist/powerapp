# -*- coding: utf-8 -*-
import re
import time
import datetime
import pytz
from logging import getLogger
from evernote.edam.error.ttypes import EDAMNotFoundException
import evernote.edam.type.ttypes as Types
from powerapp.core.todoist_utils import plaintext_content
from powerapp.sync_bridge.bridge import SyncAdapter, SyncBridge, task, undefined
from powerapp.sync_bridge.models import ItemMapping
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter
from . import utils


EPOCH = datetime.datetime(1970,1,1)
REMINDER_BASE_TIME = 946684800   # millenium


logger = getLogger(__name__)


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
    mapping = ItemMapping.objects.filter(right_id=guid, integration=integration).order_by('-id').first()
    if not mapping:
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
    ESSENTIAL_FIELDS = ['content', 'item_order', 'checked',
                        'due_date', 'date_string']

    def __init__(self, notebook_guid):
        name = '%s-%s' % (self.DEFAULT_NAME, notebook_guid)
        super(EvernoteSyncAdapter, self).__init__(name=name)
        self.notebook_guid = notebook_guid

    def push_task(self, task_id, task, extra):
        """
        Push task from Todoist to Evernote and save extra information in the
        "extra" field
        """
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

        note.title = plaintext_content(task.content, cut_url_pattern='evernote.com')
        if create:
            note.content = utils.format_note_content('')
        note.notebookGuid = self.notebook_guid

        note.attributes = Types.NoteAttributes()
        note.attributes.reminderOrder = REMINDER_BASE_TIME - task.item_order

        if task.checked:
            note.attributes.reminderDoneTime = int(time.time())
        else:
            note.attributes.reminderDoneTime = None

        if task.due_date:
            due_date_ms = int((task.due_date - EPOCH).total_seconds()) * 1000
            note.attributes.reminderTime = due_date_ms
        else:
            note.attributes.reminderTime = None

        if create:
            note = note_store.createNote(note)
        else:
            note = note_store.updateNote(note)

        new_extra = {
            'original_content': task.content,
            'original_due_date': task.due_date,
            'original_date_string': task.date_string,
        }

        return note.guid, new_extra

    def delete_task(self, task_id, extra):
        client = utils.get_evernote_client(self.user)
        note_store = client.get_note_store()
        try:
            note = note_store.getNote(task_id, True, True, False, False)
        except EDAMNotFoundException:
            return
        note.attributes.reminderTime = None
        note.attributes.reminderOrder = None
        note.attributes.reminderDoneTime = None
        note_store.updateNote(note)

    def task_from_data(self, data, extra):
        """
        Take an evernote Note and return a new generic task. data is an
        evernote Note instance

        If evernote note doesn't have to be synchronized with Todoist,
        return None.
        """
        if not data.attributes.reminderOrder:
            return None

        note_url = utils.get_note_url(data)
        content = '%s (%s)' % (note_url, data.title)

        item_order = REMINDER_BASE_TIME - data.attributes.reminderOrder
        if item_order < 1:
            item_order = 1

        if data.attributes.reminderTime is None:
            due_date = None
            date_string = None
        else:
            user = self.bridge.integration.user
            user_timezone = user.get_timezone()

            due_date = datetime.datetime.fromtimestamp(data.attributes.reminderTime / 1000)
            local_due_date = user_timezone.normalize(pytz.utc.localize(due_date))
            date_string = local_due_date.strftime('%d %b %Y at %H:%M')

            logger.debug('Timezone dance. Convert %s from UTC to %s, get %s',
                         data.attributes.reminderTime,
                         user_timezone.zone,
                         date_string)

            # we don't want to overwrite "Todoist rich date strings"
            original_due_date = extra.get('original_due_date')
            if due_date == original_due_date:
                logger.debug('Due date was not changed. Don\'t update the date')
                date_string = undefined
                due_date = undefined
            else:
                logger.debug('Due date changed from %s to %s. Update the date' % (original_due_date, due_date))

        return task(checked=data.attributes.reminderDoneTime is not None,
                    content=content, item_order=item_order, due_date=due_date,
                    date_string=date_string)
