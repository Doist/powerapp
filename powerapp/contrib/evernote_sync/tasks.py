from . import utils
from powerapp.celery_local import app
from powerapp.core.models import Integration
from powerapp.core.logging_utils import ctx
from celery.exceptions import SoftTimeLimitExceeded
from logging import getLogger


logger = getLogger(__name__)


@app.task(ignore_result=True)
def sync_evernote(integration_id):
    try:
        integration = Integration.objects.select_related('user').get(id=integration_id)
    except Integration.DoesNotExist:
        return
    with ctx(user=integration.user, integration=integration):
        try:
            utils.sync_evernote(integration)
        except SoftTimeLimitExceeded:
            logger.error('Synchronization with Evernote took too long and was aborted')
