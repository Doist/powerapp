# -*- coding: utf-8 -*-
import pytest

from powerapp.core.models.service import Service
from powerapp.core.service_collector import collect_services


@pytest.fixture
def services(db):
    collect_services()


@pytest.fixture
def catcomments_service(services):
    return Service.objects.get(label='catcomments')


def test_catcomments_has_icon(catcomments_service):
    assert catcomments_service.logo_filename == 'catcomments/logo.png'
    assert catcomments_service.logo_url == '/static/catcomments/logo.png'

def test_catcomments_urls(catcomments_service):
    assert catcomments_service.urls.add_integration == '/catcomments/integrations/add/'
