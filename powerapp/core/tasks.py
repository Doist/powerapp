# -*- coding: utf-8 -*-
from powerapp.celery_local import app
from powerapp.core.models.integration import Integration
from powerapp.core import sync


@app.task(ignore_result=True)
def initial_stateless_sync(integration_id):
    try:
        integration = Integration.objects.get(pk=integration_id)
    except Integration.DoesNotExist:
        pass
    api = sync.StatefulTodoistAPI.create(integration)
    api.sync(resource_types=['projects', 'items', 'notes'],
             save_state=False)
