from django.core.urlresolvers import reverse
from powerapp.discovery import app_discovery


def test_app_discovery_finds_catcomments():
    assert 'powerapp.contrib.catcomments' in app_discovery()


def test_reverse_url_knows_about_catcomments():
    assert reverse('catcomments:add_integration') == '/catcomments/integrations/add/'
