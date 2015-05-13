# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic import View
from powerapp.core.django_forms import IntegrationForm
from powerapp.core.models.integration import Integration
from powerapp.core.models.oauth import EMPTY_SCOPE, AccessToken


class LoginRequiredMixin(object):
    """
    A mixin to check the user is logged in
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.request.current_app = self.request.resolver_match.namespace
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class AccessTokenRequiredMixin(object):
    """
    A mixin to check the user has access token

    To make it work, the subclass has to define access_token_client (as a
    string), optionally access_token_scope, and access_token_redirect. The
    dispatcher test the database first, and if there's no access token with
    the requested client and scope, it calls the access_token_redirect()
    function.
    """
    access_token_client = None
    access_token_scope = EMPTY_SCOPE

    def dispatch(self, request, *args, **kwargs):
        # shortcut: we don't need any extra verifications
        if not self.access_token_client:
            return super(AccessTokenRequiredMixin, self).dispatch(request, *args, **kwargs)

        if not AccessToken.objects.filter(user=request.user,
                                          client=self.access_token_client,
                                          scope=self.access_token_scope).exists():
            return self.access_token_redirect(request)
        else:
            return super(AccessTokenRequiredMixin, self).dispatch(request, *args, **kwargs)

    def access_token_redirect(self, request):
        raise NotImplementedError('Implement "access_token_redirect" function '
                                  'in your subclass')



class EditIntegrationView(LoginRequiredMixin, AccessTokenRequiredMixin, View):
    """
    A view to create and modify an integration. Subclasses of this view have to
    have a `form` attrubute, which has to be a subclass of the IntegrationForm,
    and a `service_label` attribute.
    """
    form = None
    service_label = None

    def get(self, request, integration_id=None):
        integration = self.get_integration(request, integration_id)
        form = self.form_class(request.user, integration=integration)
        return render(request, self.get_template_name(), {'form': form})

    def post(self, request, integration_id=None):
        integration = self.get_integration(request, integration_id)
        form = self.form_class(request.user, integration, data=request.POST)
        if form.is_valid():
            integration = form.save()
            messages.info(request, "Integration '%s' saved" % integration.name)
            return self.on_save()
        return render(request, self.get_template_name(), {'form': form})

    def get_template_name(self):
        return '%s/edit_integration.html' % self.service_label

    def on_save(self):
        return redirect('web_index')

    @cached_property
    def form_class(self):
        """
        A wrapper around `self.form` so that you can just set up service_label,
        and the form will be created for you automatically
        """
        return self.form or type('Form', (IntegrationForm, ), {
            'service_label': self.service_label
        })

    def get_integration(self, request, integration_id):
        if integration_id:
            return get_object_or_404(Integration,
                                     id=integration_id,
                                     user_id=request.user.id)
