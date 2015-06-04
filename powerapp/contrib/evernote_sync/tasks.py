from . import utils
from powerapp.celery import app
from powerapp.core.models import Integration


@app.task(ignore_result=True)
def sync_evernote(integration_id):
    try:
        integration = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        return
    utils.sync_evernote(integration)
