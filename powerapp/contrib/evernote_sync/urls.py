# -*- coding: utf-8 -*-
from django.conf.urls import url
from .views import EditIntegrationView, authorize_evernote, authorize_evernote_done

# URL patterns have to contain at least two records: one to add integration,
# and another one to edit it, as provided below. You are welcome to add more
# endpoints if you need it.

urlpatterns = [
    url(r'^integrations/add/$', EditIntegrationView.as_view(), name='add_integration'),
    url(r'^integrations/(?P<integration_id>\d+)/$', EditIntegrationView.as_view(), name='edit_integration'),
    url(r'^authorize_evernote/', authorize_evernote, name='authorize_evernote'),
    url(r'^authorize_evernote_done/', authorize_evernote_done, name='authorize_evernote_done'),
]
