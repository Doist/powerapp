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

    def __init__(self, project_id, name=None):
        if name is None:
            name = '%s-%s' % (self.DEFAULT_NAME, project_id)
        super(TodoistSyncAdapter, self).__init__(name=name)
        self.project_id = project_id

    def push_task(self, task_id, task):
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
            return task_id

        else:
            obj = self.api.items.add(content, self.project_id, **kwargs)
            return_or_raise(self.api.commit())
            return obj['id']

    def delete_task(self, task_id):
        with self.api.autocommit():
            self.api.item_delete(task_id)


def task_from_todoist(item):
    """
    Take a Todoist item and return a new generic task
    """
    return task(checked=item['checked'], content=item['content'], date_string=item['date_string'],
                due_date=item['due_date'], in_history=item['in_history'], indent=item['indent'],
                item_order=item['item_order'], priority=item['priority'], tags=None)
