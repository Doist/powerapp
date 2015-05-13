# -*- coding: utf-8 -*-
from django.conf.urls import url
from .views import EditIntegrationView


urlpatterns = [
    url(r'^integrations/add/$', EditIntegrationView.as_view(), name='add_integration'),
    url(r'^integrations/(?P<integration_id>\d+)/$', EditIntegrationView.as_view(), name='edit_integration'),
]
