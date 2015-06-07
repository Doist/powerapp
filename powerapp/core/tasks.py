# -*- coding: utf-8 -*-
from powerapp.celery_local import app
from powerapp.core.models.integration import Integration
from powerapp.core import sync
from powerapp.core.logging_utils import ctx


@app.task(ignore_result=True)
def initial_stateless_sync(integration_id):
    """
    The sync command which is performed for "stateless integrations"
    """
    try:
        integration = Integration.objects.get(pk=integration_id)
    except Integration.DoesNotExist:
        pass
    api = sync.StatefulTodoistAPI.create(integration)
    with ctx(user=integration.user, integration=integration):
        api.sync(resource_types=['projects', 'items', 'notes'],
                 save_state=False)
