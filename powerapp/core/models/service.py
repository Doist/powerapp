import glob
import logging
import os

from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.functional import cached_property
from django.apps import apps


logger = logging.getLogger(__name__)


class Service(models.Model):
    """
    Service is a "wrapper" and enumerator for service defined in the
    `services_impl` module.

    The service is initialized with the `root` parameter, which can be a
    filename or a module directory, and optional `id` and `name` attributes

    Field examples:

    - label: catcomments
    - name: powerapp.contrib.catcomments
    - path: /full/path/to/module/named/catcomments
    """
    label = models.CharField('Service label', max_length=256, primary_key=True)
    name = models.CharField('Service name', max_length=256)
    path = models.CharField('Service path', max_length=1024)

    class Meta:
        app_label = 'core'

    def __str__(self):
        return self.name

    @property
    def app_config(self):
        """
        Return the initialized Application Config instance, connected to
        this service

        :rtype: powerapp.core.apps.ServiceAppConfig
        """
        return apps.get_app_config(self.label)

    @cached_property
    def urls(self):
        """
        A helper method returning URL for current application. Useful in
        templates like `{{ service.urls.add_integration }}`
        """
        class AttachedURL(object):
            def __init__(self, srv):
                self.srv = srv
            def __getattr__(self, item):
                return reverse('%s:%s' % (self.srv.label, item))
        return AttachedURL(self)

    @cached_property
    def logo_filename(self):
        static_root = os.path.join(self.path, 'static', self.label)
        choices = glob.glob1(static_root, 'logo.*')
        if choices:
            return os.path.join(self.label, choices[0])
        else:
            return 'common/default_logo.png'

    @cached_property
    def logo_url(self):
        return staticfiles_storage.url(self.logo_filename)

    def event_handler(self, event_name, hooks=True, sync=False):
        """ decorator for registering event handlers.

        Decorated function should accept two arguments
        - todoist_user instance
        - added/modified/deleted object

        See `TodoistUser.sync` docstring for all currently available event types
        """
        def decorator(func):
            self.event_handlers[event_name] = {'func': func,
                                               'hooks': hooks,
                                               'sync': sync}
            return func
        return decorator

    def periodic_task(self, timedelta):
        """ decorator for registering periodic tasks """
        def decorator(func):
            # we use dict instead of list to ensure uniqueness
            self.periodic_tasks[func.__name__] = (func, timedelta)
            return func
        return decorator
