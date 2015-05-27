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


@pytest.fixture
def td():
    return SampleQueue('todoist')

@pytest.fixture
def gh():
    return SampleQueue('github')

@pytest.fixture
def hub(detached_integration, td, gh):
    return SyncHub(detached_integration, [td, gh])

def test_hub_has_name(detached_integration):
    q1 = SampleQueue('q1')
    q2 = SampleQueue('q2')
    q3 = SampleQueue('q3')
    h = SyncHub(detached_integration, [q1, q2, q3])
    assert h.name == 'q1-q2-q3'


def test_queue_knows_its_hub(detached_integration):
    q1 = SampleQueue('q1')
    h = SyncHub(detached_integration, [q1])
    assert q1.hub == h


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


def test_hub_passes_tasks_through(td, gh, hub):
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


def test_hub_deletes_tasks(td, gh, hub):
    # add the task
    foo = task(content='foo')
    hub.push_task('todoist', 1, foo)

    # make sure it's there
    meta = hub.get_meta_id(td, 1)
    assert hub.get_local_id(gh, meta) in gh.storage

    # delete the task
    hub.delete_task('todoist', 1)

    # make sure the task isn't there anymore
    assert gh.storage == {}


def test_hub_updates_tasks(td, gh, hub):
    # add the task, and then update it
    hub.push_task('todoist', 1, task(content='foo'))
    hub.push_task('todoist', 1, task(content='bar'))

    # make sure "gh" has everything in sync
    meta = hub.get_meta_id(td, 1)
    obj = gh.storage[hub.get_local_id(gh, meta)]
    assert obj.content == 'bar'
