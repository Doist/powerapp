# -*- coding: utf-8 -*-
import pytest
import uuid
from powerapp.sync_hub.hub import SyncHub, SyncQueue, task, get_hash


class SampleQueue(SyncQueue):
    """
    A queue for testing purposes.
    """

    def __init__(self, name=None):
        super(SampleQueue, self).__init__(name)
        self.storage = {}

    def push_task(self, task_id, task):
        task_id = task_id or self.random_id()
        self.storage[task_id] = task
        return task_id

    def delete_task(self, task_id):
        self.storage.pop(task_id, None)

    @staticmethod
    def random_id():
        return uuid.uuid4().hex


def test_hub_has_name(detached_integration):
    q1 = SampleQueue('q1')
    q2 = SampleQueue('q2')
    q3 = SampleQueue('q3')
    hub = SyncHub(detached_integration, [q1, q2, q3])
    assert hub.name == 'q1-q2-q3'


def test_queue_knows_its_hub(detached_integration):
    q1 = SampleQueue('q1')
    hub = SyncHub(detached_integration, [q1])
    assert q1.hub == hub


def test_queue_cant_change_its_hub(detached_integration):
    q1 = SampleQueue('q1')
    SyncHub(detached_integration, [q1])
    with pytest.raises(RuntimeError):
        SyncHub(detached_integration, [q1])


def test_task_hashes():
    t1 = task(content='A')
    t2 = task(content='B', tags=None)
    t3 = task(content='B', tags=[])
    assert get_hash(t1) != get_hash(t2)
    assert get_hash(t2) == get_hash(t3)


def test_hub_passes_tasks_though(detached_integration):
    td = SampleQueue('todoist')
    gh = SampleQueue('github')
    hub = SyncHub(detached_integration, [td, gh])

    # add a task to the queue
    foo = task(content='foo')
    hub.push_task('todoist', 1, foo)

    # the task has to appear in the second storage, the first storage has
    # to be empty
    assert td.storage == {}
    assert list(gh.storage.values())[0] == foo

    # check how id mapping works
    meta = hub.get_meta_id(td, 1)
    td_id = hub.get_local_id(td, meta)
    gh_id = hub.get_local_id(gh, meta)
    assert td_id == '1'
    assert gh.storage[gh_id] == foo
