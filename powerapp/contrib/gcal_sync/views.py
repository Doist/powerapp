# -*- coding: utf-8 -*-
from logging import getLogger
from requests import HTTPError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from powerapp.core import generic_views, oauth, django_forms
from . import utils, oauth_impl
from powerapp.core.exceptions import PowerAppError
from powerapp.core.models.integration import Integration
from powerapp.core.models.user import User

logger = getLogger(__name__)


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

    try:
        integation = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        logger.debug('Integration %s does not exist. Stop channel', integration_id)
        return _stop_channel(token_data['u'], channel_id, resource_id)

    utils.sync_gcal(integation)
    return HttpResponse()


def _stop_channel(user_id, channel_id, resource_id):
    user = get_object_or_404(User, id=user_id)
    client = utils.get_authorized_client(user)
    try:
        resp = utils.json_post(client, '/channels/stop',
                               id=channel_id,
                               resouceId=resource_id)
    except HTTPError:
        # FIXME: it doesn't work :/
        pass
    return HttpResponse()
