# -*- coding: utf-8 -*-
from powerapp.core.exceptions import return_or_raise
from powerapp.sync_bridge.bridge import SyncAdapter, TASK_FIELDS, task


TODOIST_ESSENTIAL_FIELDS = TASK_FIELDS[::]
TODOIST_ESSENTIAL_FIELDS.remove('tags')


class TodoistSyncAdapter(SyncAdapter):
    """
    Sync Adapter for Todoist. Used to sync data between the chosen project in
    Todoist, and a third-party library.

    Does not support syncing of tags yet
    """
    DEFAULT_NAME = 'todoist'
    ESSENTIAL_FIELDS = TODOIST_ESSENTIAL_FIELDS

    def __init__(self, project_id):
        name = '%s-%s' % (self.DEFAULT_NAME, project_id)
        super(TodoistSyncAdapter, self).__init__(name=name)
        self.project_id = project_id

    def push_task(self, task_id, task, extra):
        content = task.content
        kwargs = {
            'checked': task.checked,
            'in_history': task.in_history,
            'indent': task.indent,
            'item_order': task.item_order,
            'priority': task.priority,
        }
        if task.due_date and task.date_string:
            kwargs.update(due_date=task.due_date, date_string=task.date_string)

        if task_id:
            self.api.item_update(task_id, content=content, **kwargs)
            return_or_raise(self.api.commit())
            return task_id, {}  # return task_id and extra

        else:
            obj = self.api.items.add(content, self.project_id, **kwargs)
            return_or_raise(self.api.commit())
            return obj['id'], {}  # return task_id and extra

    def delete_task(self, task_id, extra):
        with self.api.autocommit():
            self.api.item_delete(task_id)

    def task_from_data(self, data, extra):
        """
        Take a Todoist item (as data) and return a new generic task. "Extra"
        is not used.
        """
        return task(checked=data['checked'],
                    content=data['content'],
                    date_string=data['date_string'],
                    due_date=data['due_date'],
                    in_history=data['in_history'],
                    indent=data['indent'],
                    item_order=data['item_order'],
                    priority=data['priority'],
                    tags=None)
