import base64
import hashlib
import hmac
from itertools import groupby
import json
import binascii
import datetime
from logging import getLogger

from django.utils.encoding import force_bytes, force_text
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from powerapp.core.app_signals import ServiceAppSignals
from powerapp.core.models import Integration


FAST_SYNC_INTERVAL = datetime.timedelta(seconds=10 if settings.DEBUG else 30)


logger = getLogger(__name__)


@csrf_exempt
def accept(request):
    signature = request.META.get('HTTP_X_TODOIST_HMAC_SHA256')
    if not signature:
        return HttpResponse()

    raw_data = request.body
    if not request_valid(raw_data, signature):
        return HttpResponse()

    try:
        data = json.loads(force_text(raw_data))
    except ValueError:
        # quietly ignore invalid JSON
        return HttpResponse()

    logger.debug('Receive webhook from Todoist', extra={'data': data})

    handle_stateful_integrations(data)
    handle_stateless_integrations(data)

    # Empty 200 OK response is enough to mark webhook as processed
    # on the server side
    return HttpResponse()


def request_valid(raw_data, signature):
    """
    Helper function to test if the request is valid
    """
    try:
        raw_signature = base64.b64decode(signature)
    except (binascii.Error, TypeError):
        return False
    expected_signature = hmac.new(force_bytes(settings.TODOIST_CLIENT_SECRET),
                                  force_bytes(raw_data),
                                  hashlib.sha256)
    return expected_signature.digest() == raw_signature


def handle_stateful_integrations(data):
    user_ids = {ev['user_id'] for ev in data}
    next_sync = now() + FAST_SYNC_INTERVAL
    Integration.objects.filter(user_id__in=user_ids,
                               stateless=False,
                               service_enabled=True).update(api_next_sync=next_sync)


def handle_stateless_integrations(data):
    user_ids = {ev['user_id'] for ev in data}

    # 1. Get all integrations
    integrations = Integration.objects.filter(user_id__in=user_ids,
                                              stateless=True,
                                              service_enabled=True).order_by('user_id')

    # 2. Group them by user id
    user_integrations = {}
    for user_id, integration_subset in groupby(integrations, lambda i: i.user_id):
        user_integrations[user_id] = list(integration_subset)

    # 3. Handle events one by one
    for ev in data:
        signal_name, event_data = webhook_to_django_signal(ev)
        if not signal_name:
            continue
        user_id = ev['user_id']
        for integration in user_integrations.get(user_id, []):
            signal = integration.app_config.signals[signal_name]
            signal.fire(integration, event_data)


def webhook_to_django_signal(event):
    """
    Convert webhook name to django signal name. If None is returned, then
    there's no Django signal corresponding to an incoming event.
    """
    event_name = event['event_name']
    event_data = event['event_data']
    try:
        obj, action = event_name.split(':', 1)
    except IndexError:
        return None, None
    # item -> task
    obj = obj if obj != 'item' else 'task'

    # Todoist server-side bug workaround
    if action == 'uncompleted':
        event_data.update({'checked': False, 'in_history': False})

    # We only support added, deleted and updated events
    if action not in ('added', 'deleted'):
        action = 'updated'

    full_name = 'todoist_%s_%s' % (obj, action)
    if hasattr(ServiceAppSignals(), full_name):
        return full_name, event_data

    return None, None
