# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^integrations/add/$', views.EditIntegrationView.as_view(), name='add_integration'),
    url(r'^integrations/(?P<integration_id>\d+)/$', views.EditIntegrationView.as_view(), name='edit_integration'),
    url(r'^authorize_github/$', views.authorize_github, name='authorize_github'),
    url(r'^authorize_github/done/$', views.authorize_github_done, name='authorize_github_done'),
    url(r'^webhook/(?P<integration_id>\d+)/$', views.webhook, name='webhook'),
]
