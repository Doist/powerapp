# -*- coding: utf-8 -*-
from powerapp.core import django_forms, django_fields, generic_views


class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'catcomments'
    project = django_fields.ProjectChoiceField(label=u'Project to add kittens to')


class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'catcomments'
    form = IntegrationForm
