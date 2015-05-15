import base64
import hashlib
import hmac
import json
import binascii
import datetime
from logging import getLogger

from django.utils.encoding import force_bytes, force_text
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
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

    user_ids = {ev['user_id'] for ev in data}
    next_sync = now() + FAST_SYNC_INTERVAL
    logger.debug('Mark integrations of user with ids %s as to be processed at %s', user_ids, next_sync)
    Integration.objects.filter(user_id__in=user_ids).update(api_next_sync=next_sync)

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
