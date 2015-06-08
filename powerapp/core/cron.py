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

    For every integration object we acquire a lock, and pass this lock object
    to the worker. If lock is unable to acquire then probably another task is
    performing the sync operation right now. Don't do anything at all.
    """
    for integration in Integration.objects.filter(stateless=False,
                                                  api_next_sync__lte=now()):
        integration.api_last_sync = now()
        integration.save(update_fields=['api_last_sync'])
        run_sync_task.delay(integration.id)


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
    for ptask in PeriodicTask.objects.filter(next_run__lt=now()):
        ptask.schedule_forward()
        run_cron_task.delay(ptask.id)


@app.task(ignore_result=True)
def run_cron_task(periodic_task_id):
    """
    Run one periodic cron job for one integration
    """
    try:
        task = PeriodicTask.objects.get(id=periodic_task_id)
    except PeriodicTask.DoesNotExist:
        return
    task.run()
