# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from powerapp.core import generic_views, oauth
from . import utils, oauth_impl
from powerapp.core.models.integration import Integration



class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'gcal_sync'
    access_token_client = oauth_impl.OAUTH_CLIENT_NAME
    access_token_scope = oauth_impl.GCAL_SCOPE

    def access_token_redirect(self, request):
        return redirect('gcal_sync:authorize_gcal')


@login_required
def authorize_gcal(request):
    client = oauth.get_client_by_name(oauth_impl.OAUTH_CLIENT_NAME)
    authorize_url = client.get_authorize_url(request,
                                             access_type='offline',
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
