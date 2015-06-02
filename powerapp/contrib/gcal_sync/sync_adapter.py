# -*- coding: utf-8 -*-
from logging import getLogger
from powerapp.sync_bridge.bridge import SyncAdapter, SyncBridge, task
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter


logger = getLogger(__name__)


def build_bridge(integration, project_id):
    td = TodoistSyncAdapter(project_id)
    gc = GcalSyncAdapter()
    return SyncBridge(integration, td, gc)


class GcalSyncAdapter(SyncAdapter):
    """
    Sync Adapter for Google calendar
    """
    DEFAULT_NAME = 'gcal'
    ESSENTIAL_FIELDS = ['content', 'item_order', 'checked',
                        'due_date', 'date_string']

    def __init__(self):
        super(GcalSyncAdapter, self).__init__(name=self.DEFAULT_NAME)

    def push_task(self, task_id, task, extra):
        """
        Push task from Todoist to Google Calendar and save extra information in the
        "extra" field
        """
        return 'calendar-event-id', {'extra': 'data'}

    def delete_task(self, task_id, extra):
        """
        Delete calendar event by id
        """

    def task_from_data(self, data, extra):
        """
        Take an Google Calendar event and return a new generic task. data is a
        Google Calendar event instance

        If the event doesn't have to be synchronized with Todoist,
        return None.
        """

        return task()
