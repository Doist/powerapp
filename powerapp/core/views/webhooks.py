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

from powerapp.core.models.user import User


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
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            # this user has not been signed up to powerapp yet, just skip it
            continue

        # Mark user to sync "soon"
        user.api_next_sync = now() + FAST_SYNC_INTERVAL
        user.save()
        logger.debug('Mark user %s as to be processed at %s',
                     user, user.api_next_sync)

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
