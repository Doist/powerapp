# -*- coding: utf-8 -*-
import pytest
import uuid
from powerapp.sync_bridge.bridge import SyncBridge, SyncAdapter, task, get_hash, \
    TASK_FIELDS
from powerapp.sync_bridge.models import ItemMapping


class SampleAdapter(SyncAdapter):
    """
    A adapter for testing purposes.
    """
    DEFAULT_NAME = 'sample'

    def __init__(self, name=None):
        super(SampleAdapter, self).__init__(name)
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


class DumbSampleAdapter(SampleAdapter):
    ESSENTIAL_FIELDS = ['content']
    DEFAULT_NAME = 'dumb'


@pytest.fixture
def td():
    return SampleAdapter('todoist')

@pytest.fixture
def gh():
    return SampleAdapter('github')

@pytest.fixture
def dumb():
    return DumbSampleAdapter()

@pytest.fixture
def bridge(detached_integration, td, gh):
    return SyncBridge(detached_integration, td, gh)

@pytest.fixture
def dumb_bridge(detached_integration, td, dumb):
    return SyncBridge(detached_integration, td, dumb)


def test_bridge_has_name(bridge):
    assert bridge.name == 'todoist-github'


def test_adapter_knows_its_bridge(td, gh, bridge):
    assert td.bridge == gh.bridge == bridge


def test_adapter_cant_change_its_bridge(detached_integration):
    a1 = SampleAdapter('a1')
    a2 = SampleAdapter('a2')
    a3 = SampleAdapter('a3')
    SyncBridge(detached_integration, a1, a2)
    with pytest.raises(RuntimeError):
        SyncBridge(detached_integration, a2, a3)


def test_task_hashes():
    essential_fields = ['content', 'tags']
    t1 = task(content='A')
    t2 = task(content='B', tags=None)
    t3 = task(content='B', tags=[])
    assert get_hash(t1, essential_fields) != get_hash(t2, essential_fields)
    assert get_hash(t2, essential_fields) == get_hash(t3, essential_fields)


def test_bridge_passes_tasks_through(td, gh, bridge):
    # add a task to the adapter
    foo = task(content='foo')
    bridge.push_task(td, 1, foo)

    # check how id mapping works
    mapping = ItemMapping.objects.bridge_get(bridge, left_id=1)
    assert mapping.left_hash == get_hash(foo, essential_fields=TASK_FIELDS)
    assert mapping.left_id == '1'
    assert gh.storage[mapping.right_id] == foo


def test_bridge_deletes_tasks(td, gh, bridge):
    # add the task
    foo = task(content='foo')
    bridge.push_task(td, 1, foo)

    # make sure it's there
    assert ItemMapping.objects.bridge_get(bridge, left_id=1).right_id in gh.storage

    # delete the task
    bridge.delete_task(td, 1)

    # make sure the task isn't there anymore
    assert gh.storage == {}


def test_bridge_updates_tasks(td, gh, bridge):
    # add the task, and then update it
    bridge.push_task(td, 1, task(content='foo'))
    bridge.push_task(td, 1, task(content='bar'))

    # make sure "gh" has everything in sync
    gh_id = ItemMapping.objects.bridge_get(bridge, left_id=1).right_id
    obj = gh.storage[gh_id]
    assert obj.content == 'bar'


def test_get_hash_essential_fields():
    id2 = task(content='foo', indent=2)
    id3 = task(content='foo', indent=3)
    assert get_hash(id2, essential_fields=['content']) == get_hash(id3, essential_fields=['content'])
    assert get_hash(id2, essential_fields=['content', 'indent']) != get_hash(id3, essential_fields=['content', 'indent'])


def test_essential_fields(td, dumb, dumb_bridge):
    dumb_bridge.push_task(td, 1, task(content='foo', indent=2))
    mapping = ItemMapping.objects.bridge_get(dumb_bridge, left_id=1)
    assert mapping.left_hash != mapping.right_hash
