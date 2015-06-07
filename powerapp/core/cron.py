# -*- coding: utf-8 -*-
"""
A module containing Celery tasks for all periodic tasks we perform.

Basically, we run two types of tasks.

- For every "stateful integraion" we perform a periodic sync and generate a
  bunch of signals (item_added, item_deleted, etc...)
- If the service defines some cron job (like, polling external service), we
  perform these periodic tasks as well (PeriodicTask instances)
"""
from logging import getLogger
from powerapp.celery_local import app
from powerapp.core.models import Integration, PeriodicTask
from django.utils.timezone import now

logger = getLogger(__name__)


@app.task(ignore_result=True)
def schedule_sync_tasks():
    """
    A celery beat task which by itself does nothing but schedule a buch of
    sync tasks for execution
    """
    for _id in Integration.objects.filter(stateless=False,
                                          api_next_sync__lte=now()
                                          ).values_list('id', flat=True):
        run_sync_task.delay(_id)


@app.task(ignore_result=True)
def run_sync_task(integration_id):
    """
    Perform sync operation for "stateful integrations"
    """
    try:
        integration = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        return
    integration.api.sync(resource_types=['projects', 'items', 'notes'])


@app.task(ignore_result=True)
def schedule_cron_tasks():
    """
    A celery beat task schedules cron tasks for execution
    """
    for _id in PeriodicTask.objects.filter(next_run__lt=now()).values_list('id', flat=True):
        run_cron_task.delay(_id)


@app.task(ignore_result=True)
def run_cron_task(periodic_task_id):
    """
    Run one periodic cron job for one integration
    """
    try:
        task = PeriodicTask.objects.get(id=periodic_task_id)
    except Integration.DoesNotExist:
        return
    task.run()
