# -*- coding: utf-8 -*-
import pytest
from mock import patch
import todoist
from powerapp.core.models import Service, User, Integration
from powerapp.core.service_collector import collect_services


@pytest.fixture
def services(db):
    collect_services()


@pytest.fixture
def catcomments_service(services):
    return Service.objects.get(label='catcomments')


@pytest.yield_fixture
def quiet_sync():
    with patch.object(todoist.TodoistAPI, 'sync') as sync:
        sync.return_value = {}
        yield sync


@pytest.fixture
def detached_user(db, quiet_sync):
    return User.objects.create(id=1, email='detached@example.com', api_token='x')


@pytest.fixture
def detached_integration(detached_user, catcomments_service):
    return Integration.objects.create(name='catcomments',
                                      service=catcomments_service,
                                      user=detached_user)
