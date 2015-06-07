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
from redis.exceptions import LockError
from powerapp.celery_local import app
from powerapp.core.models import Integration, PeriodicTask
from django.utils.timezone import now
from powerapp.core.redis_utils import get_redis, serialize_lock, \
    deserialize_lock

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
    for _id in Integration.objects.filter(stateless=False,
                                          api_next_sync__lte=now()
                                          ).values_list('id', flat=True):
        lock_timeout = 5 * 60  # don't lock task for more than 5 mins
        lock_obj = get_redis().lock('integration-sync-task-%s' % _id,
                                    timeout=lock_timeout,
                                    thread_local=False)
        result = lock_obj.acquire(blocking=False)
        if result:
            # lock is ours! Schedule a task
            run_sync_task.delay(_id, serialize_lock(lock_obj))


@app.task(ignore_result=True)
def run_sync_task(integration_id, lock_obj):
    """
    Perform sync operation for "stateful integrations"
    """
    try:
        integration = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        return
    integration.api.sync(resource_types=['projects', 'items', 'notes'])
    try:
        deserialize_lock(lock_obj).release()
    except LockError as e:
        logger.warning('Unable to release the lock: %s', e)


@app.task(ignore_result=True)
def schedule_cron_tasks():
    """
    A celery beat task schedules cron tasks for execution

    To make sure we don't run the same periodic task twice in parallel, we
    use Redis locks.
    """
    for _id in PeriodicTask.objects.filter(next_run__lt=now()).values_list('id', flat=True):
        lock_timeout = 5 * 60  # don't lock task for more than 5 mins
        lock_obj = get_redis().lock('periodic-task-%s' % _id,
                                    timeout=lock_timeout,
                                    thread_local=False)
        result = lock_obj.acquire(blocking=False)
        if result:
            # lock is ours! Schedule a task
            run_cron_task.delay(_id, serialize_lock(lock_obj))


@app.task(ignore_result=True)
def run_cron_task(periodic_task_id, lock_obj):
    """
    Run one periodic cron job for one integration
    """
    try:
        task = PeriodicTask.objects.get(id=periodic_task_id)
    except Integration.DoesNotExist:
        return
    task.run()
    try:
        deserialize_lock(lock_obj).release()
    except LockError as e:
        logger.warning('Unable to release the lock: %s', e)
