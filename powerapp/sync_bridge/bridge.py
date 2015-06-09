# -*- coding: utf-8 -*-
"""
Sync bridge to perform synchronization of tasks between two independent projects
(like, between Todoist and GitHub, for example)
"""
import hashlib
import json
import datetime
from email.utils import parsedate
from logging import getLogger
from collections import namedtuple
from django.utils.encoding import force_bytes, force_text
from .models import ItemMapping
from powerapp.core.redis_utils import get_redis

logger = getLogger(__name__)


TASK_FIELDS = ['checked', 'content', 'date_string', 'due_date', 'in_history',
               'indent', 'item_order', 'priority', 'tags']


class SyncBridge(object):
    """
    Every bridge has two adapters: "left" and "right".
    """

    def __init__(self, integration, left, right, name=None):
        if name is None:
            name = '%s-%s' % (left.name, right.name)
        self.integration = integration
        self.left = left
        self.right = right
        self.adapters = [self.left, self.right]
        self.name = name
        for adapter in self.adapters:
            adapter.set_bridge(self)

    def push_task(self, source, task_id, data):
        """
        Pass through the task across the bridge. Source has to be
        the SyncAdapter object either "left" or "right"

        Task id has to be a local unique id of the task in the system backed by
        the source adapter. The task has to be a `Task` object.

        Data has to be any object of any nature. It will be later on passed
        (along with optional stored extra data) to `task_from_data` adapter
        method, which will return a Task instance.

        The function has to be called whenever a user creates or updates a
        task.
        """
        with self.lock():

            source, target, source_side, target_side = self.find_direction(source)
            mapping = self.get_mapping_by_task_id(source_side, task_id)
            if not mapping:
                mapping = self.create_mapping_by_task_id(source_side, task_id)

            # create a new task from the data
            source_extra = mapping.side(source_side).extra
            target_extra = mapping.side(target_side).extra
            task = source.task_from_data(data, source_extra)

            if task is None or is_task_undefined(task):
                return

            # calculate hashes
            source_hash = get_hash(task, source.ESSENTIAL_FIELDS)
            target_hash = get_hash(task, target.ESSENTIAL_FIELDS)

            logging_extra = {'source': source, 'target': target,
                             'mapping': mapping, 'task': task}

            mapping_source_hash = mapping.side(source_side).hash
            mapping_target_hash = mapping.side(target_side).hash
            if mapping_source_hash == source_hash or mapping_target_hash == target_hash:
                logger.debug('%s refuses to send a task %s (hashes match)',
                             source, task_id, extra=logging_extra)
                return

            logger.debug('%s pushes a task %s', source, task_id,
                         extra=logging_extra)
            target_id = mapping.side(target_side).id  # -> mapping.right_id, for example

            # push the task and get a new local id and extra data back
            new_target_id, new_target_extra = target.push_task(target_id, task, target_extra)

            if new_target_id:
                # save the updated version of the id and extra information
                mapping.side(target_side).id = force_text(new_target_id)
                mapping.side(target_side).extra = new_target_extra
                # save hashes
                mapping.side(source_side).hash = source_hash
                mapping.side(target_side).hash = target_hash
                mapping.save()
            else:
                # the receiver part is not interested in this task
                mapping.delete()

    def delete_task(self, source, task_id):
        """
        Delete a task from another side of the bridge

        The source has to be the SyncAdapter object. Task id has to be
        a local unique id of the task in the system backed by the source
        adapter.

        The function has to be called whenever a user deletes a task
        """
        with self.lock():
            source, target, source_side, target_side = self.find_direction(source)
            mapping = self.get_mapping_by_task_id(source_side, task_id)
            if not mapping:
                # the task is not known to the bridge, ignore it
                return

            # push the delete command
            target_id = mapping.side(target_side).id  # -> mapping.right_id, for example
            target_extra = mapping.side(target_side).extra
            if target_id is None:
                return

            logging_extra = {'source': source, 'target': target,
                             'mapping': mapping}

            logger.debug('%s deletes a task %s', source, task_id,
                         extra=logging_extra)
            target.delete_task(target_id, target_extra)

            # clean up all traces of the object
            mapping.delete()

    def complete_task(self, source, task_id, delete_mapping=True):
        """
        Complete a task. This method is never called by Todoist Sync Adapter,
        instead, it's used by other adapters to change the Todoist task state.

        `delete_mapping` deletes the mapping between TD and third-party service.
        Set this flag to True, if you delete the underlying object in a
        third-party service. Set it to False, if the object is still kept there
        in a sort of "inactive" (completed, archived) state, and can be
        uncompleted by a signal from Todoist later on.

        If `delete_mapping` is set to True, then once you uncomplete the item
        from Todoist, a new item will be created on a third-party service.
        """
        with self.lock():
            source, target, source_side, target_side = self.find_direction(source)
            mapping = self.get_mapping_by_task_id(source_side, task_id)
            if not mapping:
                # the task is not known to the bridge, ignore it
                return

            # push the complete command
            target_id = mapping.side(target_side).id  # -> mapping.right_id, for example
            target_extra = mapping.side(target_side).extra
            if target_id:
                logger.debug('%s completes a task %s', source, task_id,
                             extra={'source': source, 'target': target, 'mapping': mapping})
                target.complete_task(target_id, target_extra)

            # clean up all traces of the object
            if delete_mapping:
                mapping.delete()

    def find_direction(self, source):
        if source == self.left:
            return self.left, self.right, 'left', 'right'
        elif source == self.right:
            return self.right, self.left, 'right', 'left'
        raise RuntimeError("Unknown source %r" % source)

    def get_mapping_by_task_id(self, side, task_id):
        """
        Helper function to find the mapping, if several mappings found, use the last one
        """
        kw = {'%s_id' % side: task_id}  # i.e. left_id: 15
        return ItemMapping.objects.bridge_filter(self, **kw).order_by('-id').first()

    def create_mapping_by_task_id(self, side, task_id):
        """
        Helper function to create a new mapping
        """
        kw = {'%s_id' % side: task_id}  # i.e. left_id: 15
        return ItemMapping.objects.bridge_create(self, **kw)

    def lock(self):
        """
        Internal function returning a "global redis lock" to make sure we
        perform only one sync operation at a time.
        """
        lock_name = 'sync-bridge-%s-%s' % (self.integration.id, self.name)
        lock_timeout = 60 * 5  # no more than 5 mins per sync operation
        blocking_timeout = 30  # no more than 30 seconds waiting for the lock
        return get_redis().lock(lock_name, timeout=lock_timeout,
                                blocking_timeout=blocking_timeout)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self)


class SyncAdapter(object):
    """
    Abstract `bridge adapter` accepting and executing commands
    """
    DEFAULT_NAME = 'default'
    ESSENTIAL_FIELDS = TASK_FIELDS

    def __init__(self, name=None):
        self.name = name or self.DEFAULT_NAME
        self.bridge = None

    def push_task(self, task_id, task, extra):
        """
        Add task to the storage
        """
        raise NotImplementedError("Has to be implemented in a subclass")

    def delete_task(self, task_id, extra):
        """
        Delete task from the storage
        """
        raise NotImplementedError("Has to be implemented in a subclass")

    def complete_task(self, task_id, extra):
        """
        Complete the task in the storage
        """
        raise NotImplementedError("Has to be implemented in a subclass")

    def task_from_data(self, data, extra):
        """
        Convert "raw application data" and optional extra information to
        a generic task objects. If None is returned, then the task doesn't have
        to be forwarded at all.
        """
        raise NotImplementedError("Has to be implemented in a subclass")

    def set_bridge(self, bridge):
        if self.bridge and bridge != self.bridge:
            raise RuntimeError('Unable to set the bridge for the adapter')
        self.bridge = bridge

    @property
    def user(self):
        """:rtype: powerapp.core.models.User"""
        return self.bridge.integration.user

    @property
    def api(self):
        """:rtype: powerapp.core.sync.StatelessTodoistAPI"""
        return self.bridge.integration.api

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self)


# A "more or less generic" task object. Used as a container to move tasks
# around. Actually, it's based on a copy-paste of a Todoist task, bit in
# your integration you don't always have to use all these fields. Just use
# ones that make sense for your particular case

Task = namedtuple('Task', TASK_FIELDS)


# undefined is a special object to mark fields which don't have to be changed
# on sync
class Undefined(object):
    def __repr__(self):
        return '(undefined)'
    def __str__(self):
        return '(undefined)'
undefined = Undefined()


def defined(*values):
    """
    Helper function which returns the first non-undefined object. Can be used
    as a replacement `value or default_value` like::

        defined(value, default_value)
    """
    for v in values:
        if v is not undefined:
            return v


def task(checked=undefined,
         content=undefined,
         date_string=undefined,
         due_date=undefined,
         in_history=undefined,
         indent=undefined,
         item_order=undefined,
         priority=undefined,
         tags=undefined):
    """
    A helper function to create tasks
    """
    # for the sake of unification (we need to have equal hashes),
    # make sure we have same types for empty values
    if checked is not undefined:
        checked = bool(checked)
    if content is not undefined:
        content = content or ''
    if date_string is not undefined:
        date_string = date_string or None
    if due_date is not undefined:
        due_date = normalize_due_date(due_date)
    if in_history is not undefined:
        in_history = bool(in_history)
    if indent is not undefined:
        indent = int(indent)
    if item_order is not undefined:
        item_order = int(item_order)
    if priority is not undefined:
        priority = int(priority)
    if tags is not undefined:
        tags = tags or []

    # create a task object itself
    return Task(checked, content, date_string, due_date, in_history,
                indent, item_order, priority, tags)


def is_task_undefined(task):
    return all(i is undefined for i in task)


def normalize_due_date(due_date):
    """
    Make an attempt to parse a due date: convert it from the string or integer
    to datetime object
    """
    if not due_date:
        return None

    if isinstance(due_date, str):
        parsed_due_date = parsedate(due_date)
        if parsed_due_date:
            return datetime.datetime(*parsed_due_date[:6])
    elif isinstance(due_date, int):
        return datetime.datetime.fromtimestamp(due_date)

    if not isinstance(due_date, datetime.datetime):
        raise RuntimeError('Due date has to be None or a datetime object')

    due_date = due_date.replace(tzinfo=None)
    return due_date


def get_hash(obj, essential_fields):
    subset = {k: v for k, v in obj._asdict().items() if k in essential_fields}
    str_obj = json.dumps(subset, separators=',:', sort_keys=True, default=json_default)
    return hashlib.sha256(force_bytes(str_obj)).hexdigest()


def json_default(obj):
    if obj is undefined:
        # we need something to be clearly distinguishable from null,
        # 0 or empty strings
        return {'object': 'undefined'}
    if isinstance(obj, datetime.date):
        return obj.strftime('%Y-%m-%d')
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%dT%TZ')
    raise TypeError('%r is not JSON serializable' % obj)
