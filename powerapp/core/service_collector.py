# -*- coding: utf-8 -*-
from logging import getLogger

from django.apps import apps

from powerapp.core.models.service import Service


logger = getLogger(__name__)


def collect_services():
    app_configs = get_service_app_configs()
    services = get_services()

    # add new services, if there are some unknown or modify their data
    for label, config in app_configs.items():
        if label not in services.keys():
            Service.objects.create(label=config.label,
                                   name=config.name,
                                   path=config.path)
            logger.info('Created service %s', label)
        else:
            service = services[label]
            if service.name != config.name or service.path != config.path:
                service.name = config.name
                service.path = config.path
                service.save()
                logger.info('Updated service %s', label)

    # delete services which aren't known anymore
    for label, service in services.items():
        if label not in app_configs.keys():
            service.delete()
            logger.info('Deleted service %s', label)


def get_service_app_configs():
    """
    Return a dict of application configs known by Django
    """
    ret = {}
    for config in apps.get_app_configs():
        if getattr(config, 'service', None):
            ret[config.label] = config
    return ret


def get_services():
    """
    Return the list of services we know about
    """
    return {s.label: s for s in Service.objects.all()}
