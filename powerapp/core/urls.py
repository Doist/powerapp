# -*- coding: utf-8 -*-
from django.conf.urls import url
from powerapp.core.views import web, webhooks


urlpatterns = [
    # web
    url(r'^$', web.dashboard, name='web_index'),
    url(r'^services/$', web.services, name='web_services'),
    url(r'^login/$', web.login, name='web_login'),
    url(r'^logout/$', web.logout, name='web_logout'),
    url(r'^oauth2cb/$', web.oauth2cb, name='web_oauth2cb'),
    url(r'delete_integration/(?P<service_id>[\w\-]+)/(?P<integration_id>\d+)/$',
        web.delete_integration, name='web_delete_integration'),
    url(r'edit_integration/(?P<service_id>[\w\-]+)/(?P<integration_id>\d+)/$',
        web.edit_integration, name='web_edit_integration'),

    # webhooks
    url(r'^webhooks/accept/$', webhooks.accept, name='webhooks_accept'),
]
