# -*- coding: utf-8 -*-
from django import forms
from powerapp.core.models import Service, Integration


class IntegrationForm(forms.Form):
    """
    Base integration form. Accepts two extra arguments: user and optional
    integration object. When the integration is None, it is supposed that
    the integration is added, otherwise the integration is changed.

    When you subclass your form:

    - define a service_label attribute
    - provide any extra fields you want, they're all will be stored as
      integration settings
    """
    service_label = None
    name = forms.CharField(label=u'Integration name')

    def __init__(self, user, integration=None, *args, **kwargs):
        self.user = user
        self.integration = integration
        self.service = Service.objects.get(label=self.service_label)

        # set up initial values for the form
        initial = kwargs.get('initial') or {}
        if integration:
            assert integration.service_id == self.service_label
            initial.update(dict(integration.settings, name=integration.name))
        else:
            initial.update(name=self.service.app_config.verbose_name)
        kwargs['initial'] = initial

        # init the form itself
        super(IntegrationForm, self).__init__(*args, **kwargs)

        # populate instance fields with user data
        self.populate_with_user()

    def populate_with_user(self):
        for field_obj in self.fields.values():
            if hasattr(field_obj, 'populate_with_user'):
                field_obj.populate_with_user(self.user)

    def save(self):
        if not self.integration:
            self.integration = Integration(service_id=self.service_label,
                                           user=self.user)
        integration_settings = dict(self.cleaned_data)
        self.integration.name = integration_settings.pop('name')
        self.integration.save()

        self.integration.update_settings(**integration_settings)
        return self.integration
