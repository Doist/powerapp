# -*- coding: utf-8 -*-
from django.conf.urls import url
from .views import EditIntegrationView, authorize_gcal, sync_now

urlpatterns = [
    url(r'^integrations/add/$', EditIntegrationView.as_view(), name='add_integration'),
    url(r'^integrations/(?P<integration_id>\d+)/$', EditIntegrationView.as_view(), name='edit_integration'),
    url(r'^authorize_gcal/', authorize_gcal, name='authorize_gcal'),
    url(r'^sync_now/(?P<integration_id>\d+)/$', sync_now, name='sync_now'),
]
