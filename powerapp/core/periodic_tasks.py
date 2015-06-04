# -*- coding: utf-8 -*-
from django.utils.timezone import now
from powerapp.core.models import Service, Integration, PeriodicTask
from logging import getLogger


logger = getLogger(__name__)


def add(integration):
    """
    Add all periodic tasks for the given integration
    """
    to_add = []
    for task_name in integration.service.app_config.periodic_tasks.keys():
        to_add.append(PeriodicTask(integration=integration,
                                   name=task_name, next_run=now()))
        logger.info('Task %s:%s scheduled for adding',
                    integration.service_id, task_name)
    if to_add:
        PeriodicTask.objects.bulk_create(to_add)


def sync():
    """
    Make sure every integration has a periodic task. We add new periodic tasks
    if we find something new, we delete outdated periodic tasks, if integration
    doesn't have such tasks anymore
    """
    serice_periodic_tasks = {}

    for service in Service.objects.all():
        serice_periodic_tasks[service.label] = service.app_config.periodic_tasks.keys()

    to_delete = []
    to_add = []

    for integration in Integration.objects.prefetch_related('periodictask_set').filter(service_enabled=True):
        expected_tasks = serice_periodic_tasks[integration.service_id]
        actual_tasks = {t.name: t.id for t in integration.periodictask_set.all()}

        for actual_task_name, actual_task_id in actual_tasks.items():
            if actual_task_name not in expected_tasks:
                to_delete.append(actual_task_id)
                logger.info('Task %s:%s scheduled for removal',
                            integration.service_id, actual_task_name)

        for expected_task in expected_tasks:
            if expected_task not in actual_tasks.keys():
                to_add.append(PeriodicTask(integration=integration,
                                           name=expected_task,
                                           next_run=now()))
                logger.info('Task %s:%s scheduled for adding',
                            integration.service_id, expected_task)

    if to_add:
        PeriodicTask.objects.bulk_create(to_add)

    if to_delete:
        PeriodicTask.objects.filter(id__in=to_delete).delete()


def run_pending():
    """
    Run all pending periodic tasks
    """
    for task in get_pending():
        task.run()


def get_pending():
    """ Iterator returning periodic tasks to be executed

    :rtype: Iterator[PeriodicTask]
    """
    for task in PeriodicTask.objects.filter(next_run__lt=now()):
        yield task
