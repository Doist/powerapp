# -*- coding: utf-8 -*-
import re
from collections import namedtuple
from importlib import import_module
from logging import getLogger

from django import apps
from django.conf import settings
from django.conf.urls import url, include
from django.dispatch import Signal
from django.utils.six import with_metaclass
from powerapp.core import sync
from powerapp.core.models.integration import Integration


logger = getLogger(__name__)


class LoadModuleMixin(object):
    """
    A mixin for an app to load any of its submodule
    """

    def load_module(self, name, quiet=True):
        """
        A helper to load any app's submodule by its name
        """
        full_name = '%s.%s' % (self.name, name)
        try:
            return import_module(full_name)
        except ImportError:
            if quiet:
                return None
            raise


class AppConfig(LoadModuleMixin, apps.AppConfig):
    """
    App Config for the powerapp.core app itself
    """
    name = 'powerapp.core'
    verbose_name = 'PowerApp core application'

    def ready(self):
        # import the submodule with signal handlers
        self.load_module('signals')
        # import the submodule with OAuth implementations
        self.load_module('oauth_impl')


class ServiceAppConfigMeta(type):
    """
    A metaclass to create the ServiceAppConfig.

    We need this for two reasons:

    1. to create new objects for every signal in every subclass
    2. to have a personal periodic task registry for every subclass we have
    """

    def __new__(mcs, name, bases, attrs):
        attrs['signals'] = ServiceAppSignals()
        attrs['periodic_tasks'] = {}
        return type.__new__(mcs, name, bases, attrs)


class ServiceAppSignals(object):
    """
    The registry of all signals which the service app can emit.
    """
    SYNC_SIGNAL_ARGS = ['integration', 'obj']

    def __init__(self):
        self.todoist_project_added = Signal(providing_args=self.SYNC_SIGNAL_ARGS)
        self.todoist_project_updated = Signal(providing_args=self.SYNC_SIGNAL_ARGS)
        self.todoist_project_deleted = Signal(providing_args=self.SYNC_SIGNAL_ARGS)

        self.todoist_task_added = Signal(providing_args=self.SYNC_SIGNAL_ARGS)
        self.todoist_task_updated = Signal(providing_args=self.SYNC_SIGNAL_ARGS)
        self.todoist_task_deleted = Signal(providing_args=self.SYNC_SIGNAL_ARGS)

        self.todoist_note_added = Signal(providing_args=self.SYNC_SIGNAL_ARGS)
        self.todoist_note_updated = Signal(providing_args=self.SYNC_SIGNAL_ARGS)
        self.todoist_note_deleted = Signal(providing_args=self.SYNC_SIGNAL_ARGS)

    def __getitem__(self, item):
        """
        :rtype: Signal
        """
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError('Signal %r not found' % item)


class ServiceAppConfig(with_metaclass(ServiceAppConfigMeta, LoadModuleMixin, apps.AppConfig)):
    """
    Base class for the application config object of services
    """
    #: A special flag to denote that current Django app represents a
    #: powerapp service
    service = True

    #: The registry of powerapp signals. We overwrite it in metaclass anyway,
    #: but this way it provides hints for IDEs
    signals = ServiceAppSignals()

    #: The registry of periodic tasks. We overwrite it in metaclass as well
    periodic_tasks = {}
    """:type: dict[str,PeriodicTaskFun]"""

    def urlpatterns(self):
        """
        Returns the list of URL patterns which have to be added to main urls.py

        By default returns a sigle URL pattern which mounts app's urls.py as
        under the app's label path. Most likely you don't need to edit this
        function.
        """
        regex = r'^%s/' % self.label
        urls_module = '%s.urls' % self.name
        ns = self.label
        return [url(regex, include(urls_module, namespace=ns, app_name=ns))]

    def ready(self):
        """
        A signal called by the constructor once the app instance is ready
        (once it's registered)
        """
        # export app settings
        self.export_settings()
        # import the submodule with signal handlers
        self.load_module('signals')

    def export_settings(self):
        re_variable = re.compile(r'^[A-Z0-9_]+$')
        for key, value in self.__class__.__dict__.items():
            if re_variable.match(key) and not hasattr(settings, key):
                setattr(settings, key, value)

    @classmethod
    def periodic_task(cls, delta, name=None):
        """
        A decorator to add a periodic task. Decorated function has to accept
        two arguments: user and integration objets
        """
        def decorator(func):
            registry_name = name or '%s.%s' % (func.__module__, func.__name__)
            cls.periodic_tasks[registry_name] = PeriodicTaskFun(func, delta, registry_name)
            return func
        return decorator


#: A wrapper for periodic tasks
PeriodicTaskFun = namedtuple('PeriodicTaskFun', ['func', 'delta', 'name'])
