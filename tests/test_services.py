# -*- coding: utf-8 -*-
def test_catcomments_has_icon(catcomments_service):
    assert catcomments_service.logo_filename == 'catcomments/logo.png'
    assert catcomments_service.logo_url == '/static/catcomments/logo.png'

def test_catcomments_urls(catcomments_service):
    assert catcomments_service.urls.add_integration == '/catcomments/integrations/add/'
