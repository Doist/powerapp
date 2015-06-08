# -*- coding: utf-8 -*-
from logging import getLogger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from powerapp.core import generic_views, oauth, django_forms
from . import utils, oauth_impl, tasks
from powerapp.core.exceptions import PowerAppError
from powerapp.core.integration_utils import schedule_with_rate_limit
from powerapp.core.models.integration import Integration

logger = getLogger(__name__)


class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'gcal_sync'

    def post_save(self):
        if self.integration_created:
            return tasks.create_calendar.si(self.integration.id)


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
    authorize_url = client.get_authorize_url(access_type='offline',
                                             approval_prompt='force')
    client.set_state(request)
    context = {'authorize_url': authorize_url}
    return render(request, 'gcal_sync/authorize_gcal.html', context)


@login_required
@require_POST
def sync_now(request, integration_id):
    get_object_or_404(Integration, id=integration_id, user_id=request.user.id)
    subtask = tasks.sync_gcal.s(integration_id)
    schedule_with_rate_limit(integration_id, 'last_sync', subtask)
    messages.info(request, 'Synchronization with Google Calendar scheduled')
    return redirect('gcal_sync:edit_integration', integration_id)


@csrf_exempt
def accept_webhook(request, integration_id):
    """
    Google Calendar webhook handler

    For more details see
    https://developers.google.com/google-apps/calendar/v3/push?hl=en_US#receiving-notifications
    """
    try:
        channel_id = request.META['HTTP_X_GOOG_CHANNEL_ID']
        resource_id = request.META['HTTP_X_GOOG_RESOURCE_ID']
        resource_state = request.META['HTTP_X_GOOG_RESOURCE_STATE']
        resource_uri = request.META['HTTP_X_GOOG_RESOURCE_URI']
        token = request.META['HTTP_X_GOOG_CHANNEL_TOKEN']
    except KeyError:
        # not a google request
        return HttpResponse()

    try:
        token_data = utils.validate_webhook_token(token)
    except PowerAppError:
        logger.debug("Invalid token %s. Quietly ignore", token)
        return HttpResponse()

    logger.debug('Received webhook from Google Calendar, '
                 'channel_id=%s, token=%s, resource: (id=%s, state=%s, uri=%s)',
                 channel_id, token, resource_id, resource_state, resource_uri)

    if Integration.objects.filter(id=integration_id).exists():
        subtask = tasks.sync_gcal.s(integration_id)
        schedule_with_rate_limit(integration_id, 'last_sync', subtask)
    else:
        tasks.stop_channel.delay(token_data['u'], channel_id, resource_id)

    return HttpResponse()
