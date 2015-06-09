# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from powerapp.contrib.evernote_sync.models import EvernoteAccountCache
from powerapp.core import generic_views
from . import forms, utils, tasks
from powerapp.core.integration_utils import schedule_with_rate_limit
from powerapp.core.models.integration import Integration
from powerapp.core.models.oauth import OAuthToken
from powerapp.core.web_utils import build_absolute_uri
from powerapp.sync_bridge.models import ItemMapping


class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'evernote_sync'
    access_token_client = utils.ACCESS_TOKEN_CLIENT
    form = forms.IntegrationForm

    def access_token_redirect(self, request):
        return redirect('evernote_sync:authorize_evernote')


@login_required
def authorize_evernote(request):
    client = utils.get_unauthorized_evernote_client()
    callback_url = build_absolute_uri(reverse('evernote_sync:authorize_evernote_done'))
    request_token = client.get_request_token(callback_url)
    request.session['evernote_request_token'] = request_token
    context = {'auth_uri': client.get_authorize_url(request_token)}
    return render(request, 'evernote_sync/authorize_evernote.html', context)


@login_required
def authorize_evernote_done(request):

    request_token = request.session.pop('evernote_request_token', None)
    if not request_token:
        return redirect('evernote_sync:authorize_evernote')

    error = None
    access_token = None

    oauth_token = request.GET.get('oauth_token')
    oauth_verifier = request.GET.get('oauth_verifier')

    if not oauth_token:
        error = u'Invalid response from Evernote'
    elif oauth_token != request_token.get('oauth_token'):
        error = u'Unexpected response from Evernote'
    elif not oauth_verifier:
        error = u'Access to Evernote rejected'

    if not error:
        client = utils.get_unauthorized_evernote_client()
        oauth_token_secret = request_token['oauth_token_secret']
        try:
            access_token = client.get_access_token(oauth_token,
                                                   oauth_token_secret,
                                                   oauth_verifier)
        except ValueError as e:
            error = strip_tags(str(e))

    if error:
        return render(request, 'evernote_sync/authorize_evernote_done.html',
                      {'error': error})

    OAuthToken.register(request.user, utils.ACCESS_TOKEN_CLIENT, access_token)
    return redirect('evernote_sync:add_integration')


@login_required
@require_POST
def sync_now(request, integration_id):
    integration = get_object_or_404(Integration,
                                    id=integration_id,
                                    user_id=request.user.id)
    tasks.sync_evernote.delay(integration.id)
    messages.info(request, 'Synchronization with Evernote scheduled')
    return redirect('evernote_sync:edit_integration', integration.id)


@csrf_exempt
def accept_webhook(request, webhook_secret_key):
    """
    Webhooks recipient, as described here:

    https://dev.evernote.com/doc/articles/polling_notification.php
    """
    if settings.EVERNOTE_WEBHOOK_SECRET_KEY != webhook_secret_key:
        # not an Evernote request
        return HttpResponse()

    # "Webhook reasons" we react on: Evernote note created, Evernote note
    # updated. Everything else is quietly ignored
    reasons = {'create', 'update'}
    reason = request.GET.get('reason')
    if reason not in reasons:
        return HttpResponse()

    # We react on userId and notebookGuid. If we have an integration to
    # sync, schedule a new evernote synchronization, but make sure we don't
    # perform sync more often than once in a minute
    try:
        user_id = int(request.GET.get('userId'))
    except (TypeError, ValueError):
        return HttpResponse()
    notebook_guid = request.GET.get('notebookGuid')

    # most likely, it's going to be no more than one cache object, and no
    # more than one integration. Two or more Evernote accounts connected to
    # the same client, or more than one Evernote integration per account
    # is an exception
    for cache in (EvernoteAccountCache.objects
                          .filter(evernote_user_id=user_id)
                          .select_related('user')):
        for integration in cache.user.integration_set.filter(service_id='evernote_sync'):
            notebooks = integration.settings.get('evernote_notebooks') or []
            if notebook_guid in notebooks:
                subtask = tasks.sync_evernote.s(integration.id)
                schedule_with_rate_limit(integration.id, 'last_sync', subtask)

    return HttpResponse()
