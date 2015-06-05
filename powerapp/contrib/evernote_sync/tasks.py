from . import utils
from powerapp.celery_local import app
from powerapp.core.models import Integration
from powerapp.core.logging_utils import ctx


@app.task(ignore_result=True)
def sync_evernote(integration_id):
    try:
        integration = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        return
    with ctx(user=integration.user, integration=integration):
        utils.sync_evernote(integration)
