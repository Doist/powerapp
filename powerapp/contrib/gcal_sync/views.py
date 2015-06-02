# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from powerapp.core import generic_views, oauth, django_forms
from . import utils, oauth_impl
from powerapp.core.models.integration import Integration



class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'gcal_sync'

    def post_save(self):
        if self.integration_created:
            calendar = utils.get_or_create_todoist_calendar(self.integration)
            utils.subscribe_to_todoist_calendar(self.request, self.integration, calendar)


class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'gcal_sync'
    access_token_client = oauth_impl.OAUTH_CLIENT_NAME
    access_token_scope = oauth_impl.GCAL_SCOPE
    form = IntegrationForm

    def access_token_redirect(self, request):
        return redirect('gcal_sync:authorize_gcal')


@login_required
def authorize_gcal(request):
    client = oauth.get_client_by_name(oauth_impl.OAUTH_CLIENT_NAME)
    authorize_url = client.get_authorize_url(request,
                                             access_type='offline',
                                             approval_prompt='force',
                                             login_hint=request.user.email)
    client.set_state(request)
    context = {'authorize_url': authorize_url}
    return render(request, 'gcal_sync/authorize_gcal.html', context)


@login_required
@require_POST
def sync_now(request, integration_id):
    integration = get_object_or_404(Integration,
                                    id=integration_id,
                                    user_id=request.user.id)
    utils.sync_gcal(integration)
    messages.info(request, 'Synchronization performed')
    return redirect('gcal_sync:edit_integration', integration.id)


@csrf_exempt
def accept_webhook(request, integration_id):
    return HttpResponse()
