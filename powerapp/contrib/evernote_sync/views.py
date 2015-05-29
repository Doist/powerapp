# -*- coding: utf-8 -*-
from powerapp.core import generic_views
from . import forms


class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'evernote_sync'
    form = forms.IntegrationForm
