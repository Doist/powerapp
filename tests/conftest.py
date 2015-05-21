# -*- coding: utf-8 -*-
import pytest
from powerapp.core.models import Service
from powerapp.core.service_collector import collect_services


@pytest.fixture
def services(db):
    collect_services()


@pytest.fixture
def catcomments_service(services):
    return Service.objects.get(label='catcomments')
