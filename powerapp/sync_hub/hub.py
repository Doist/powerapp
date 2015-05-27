# -*- coding: utf-8 -*-
"""
Sync bridge to perform synchronization of tasks between two (or more) items
"""
import hashlib
import json
import datetime
from collections import namedtuple
from django.utils.encoding import force_bytes, force_text
from .models import MetaItem, LocalItem


class SyncHub(object):

    def __init__(self, integration, queues, name=None):
        if name is None:
            name = '-'.join([q.name for q in queues])
        self.integration = integration
        self.queues = queues
        self.queues_dict = {q.name: q for q in queues}
        self.name = name
        for queue in queues:
            queue.set_hub(self)

    def queue(self, name):
        """ return queue by its name """
        return self.queues_dict[name]

    def push_task(self, source, task_id, task):
        """
        Push the task to all queues on behalf of `source`

        The source can be a queue name, or a queue object. Task id has to be
        a local unique id of the task in the system backed by the source
        queue. The task has to be a `Task` object.

        The function has to be called whenever a user creates or updates a
        task.
        """
        source = self.get_source(source)

        task_hash = get_hash(task)
        meta_id = self.get_meta_id(source, task_id,
                                   item_hash=task_hash,
                                   create=True)

        id_mapping = self.get_id_mapping(meta_id)
        for queue in self.queues:
            if queue == source:
                continue
            local_id = id_mapping.get(queue.name, None)
            new_local_id = queue.push_task(local_id, task)
            self.replace_local_id(queue, meta_id, local_id, new_local_id)

    def delete_task(self, source, task_id):
        """
        Delete a task from all other parties

        The source can be a queue name, or a queue object. Task id has to be
        a local unique id of the task in the system backed by the source
        queue.

        The function has to be called whenever a user deletes a task
        """
        source = self.get_source(source)

        meta_id = self.get_meta_id(source, task_id)
        if not meta_id:
            # the task is not known to the hub, ignore it
            return

        id_mapping = self.get_id_mapping(meta_id)
        for queue in self.queues:
            if queue == source:
                continue
            local_id = id_mapping.get(queue.name, None)
            if local_id:
                # otherwise the task is not known to that queue,
                # nothing to delete
                queue.delete_task(local_id)

        # clean up all traces of the object
        self.delete_id_mapping(meta_id)

    def get_id_mapping(self, meta_id):
        """
        Given the meta id, return the dict with the mapping
        {'queue_name': <its local id>}
        """
        items = LocalItem.objects.hub_filter(self, meta_item_id=meta_id)
        return {i[0]: i[1] for i in items.values_list('queue_name', 'local_id')}

    def delete_id_mapping(self, meta_id):
        # it has to be deleted with all local ids as well
        MetaItem.objects.hub_delete(self, id=meta_id)

    def get_meta_id(self, queue, local_id, item_hash=None, create=False):
        """
        Given the queue object and a local id of the task inside a queue,
        return the "task meta id". If no such meta id found, create one, attach
        local id and meta id, and return it.
        """
        local_id = force_text(local_id)

        try:
            obj = LocalItem.objects.hub_get(self, queue_name=queue.name,
                                            local_id=local_id)
            return obj.meta_item_id
        except LocalItem.DoesNotExist:
            if create:
                meta_item = MetaItem.objects.hub_create(self, item_hash=item_hash)
                LocalItem.objects.hub_create(self,
                                             queue_name=queue.name,
                                             local_id=local_id,
                                             meta_item=meta_item)
                return meta_item.id

    def replace_local_id(self, queue, meta_id, local_id, new_local_id):
        if new_local_id == local_id:
            return

        if local_id is not None:
            LocalItem.objects.hub_delete(self,
                                         queue_name=queue.name,
                                         local_id=local_id,
                                         meta_item_id=meta_id)
        LocalItem.objects.hub_create(self,
                                     queue_name=queue.name,
                                     local_id=new_local_id,
                                     meta_item_id=meta_id)

    def get_local_id(self, queue, meta_id):
        return LocalItem.objects.hub_get(self,
                                         queue_name=queue.name,
                                         meta_item_id=meta_id).local_id

    def get_source(self, source):
        if not isinstance(source, SyncQueue):
            source = self.queue(source)
        return source

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self)


class SyncQueue(object):
    """
    Abstract `hub queue` accepting and executing commands
    """
    DEFAULT_NAME = 'default'

    def __init__(self, name=None):
        self.name = name or self.DEFAULT_NAME
        self.hub = None

    def push_task(self, task_id, task):
        """
        Add task to the storage
        """
        pass

    def delete_task(self, task_id):
        """
        Delete task from the storage
        """
        pass

    def set_hub(self, hub):
        if self.hub and hub != self.hub:
            raise RuntimeError('Unable to set the hub for the queue')
        self.hub = hub

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self)


# A "more or less generic" task object. Used as a container to move tasks
# around. Actually, it's based on a copy-paste of a Todoist task, bit in
# your integration you don't always have to use all these fields. Just use
# ones that make sense for your particular case
Task = namedtuple('Task', ['checked', 'content', 'date_string', 'due_date',
                           'in_history', 'indent', 'item_order', 'priority',
                           'tags'])


def task(checked=False, content='', date_string=None, due_date=None,
         in_history=False, indent=0, item_order=0, priority=0, tags=None):
    """
    A helper function to create tasks
    """
    # for the sake of unification (we need to have equal hashes),
    # make sure we have same types for empty values
    checked = bool(checked)
    content = content or ''
    date_string = date_string or None
    due_date = due_date or None
    in_history = bool(in_history)
    indent = int(indent)
    item_order = int(item_order)
    priority = int(priority)
    tags = tags or []

    # create a task object itself
    return Task(checked, content, date_string, due_date, in_history,
                indent, item_order, priority, tags)


def get_hash(obj):
    str_obj = json.dumps(obj, separators=',:', sort_keys=True,
                         default=json_default)
    return hashlib.sha256(force_bytes(str_obj)).hexdigest()


def json_default(obj):
    if isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%dT%TZ')
    raise TypeError('%r is not JSON serializable' % obj)
