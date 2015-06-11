# -*- coding: utf-8 -*-
from django.dispatch import Signal
from logging import getLogger
from powerapp.core.logging_utils import ctx
from todoist import models

logger = getLogger(__name__)


class TodoistSyncSignal(Signal):

    SYNC_SIGNAL_ARGS = ['integration', 'obj']

    def __init__(self, name, model):
        super(TodoistSyncSignal, self).__init__(providing_args=self.SYNC_SIGNAL_ARGS)
        self.name = name
        self.model = model

    def fire(self, integration, obj):
        """
        A wrapper around `send_robust` with logging and type conversion
        """
        if self.has_listeners():
            # type conversion: we don't want plain dict as an obj
            if not isinstance(obj, self.model):
                obj = self.model(obj, integration.api)

            # note: we use "select_related('user')" to make sure we don't
            # have a separate query for integration.user over here
            with ctx(integration=integration, user=integration.user):
                extra = {'signal_name': self.name, 'obj': obj}
                logger.debug('Send Todoist event', extra=extra)
                resp = self.send_robust(None, integration=integration, obj=obj)
                for func, item in resp:
                    # log exceptions
                    if isinstance(item, Exception):
                        exc_info = (item.__class__, item, item.__traceback__)
                        logger.error('Todoist event handler %s() raises %r',
                                     func.__name__, item,
                                     exc_info=exc_info,
                                     extra=dict(extra, func_name=func.__name__))


class ServiceAppSignals(object):
    """
    The registry of all signals which the service app can emit.
    """

    def __init__(self):
        self.todoist_project_added = TodoistSyncSignal('todoist_project_added', models.Project)
        self.todoist_project_updated = TodoistSyncSignal('todoist_project_updated', models.Project)
        self.todoist_project_deleted = TodoistSyncSignal('todoist_project_deleted', models.Project)

        self.todoist_task_added = TodoistSyncSignal('todoist_task_added', models.Item)
        self.todoist_task_updated = TodoistSyncSignal('todoist_task_updated', models.Item)
        self.todoist_task_deleted = TodoistSyncSignal('todoist_task_deleted', models.Item)

        self.todoist_note_added = TodoistSyncSignal('todoist_note_added', models.Note)
        self.todoist_note_updated = TodoistSyncSignal('todoist_note_updated', models.Note)
        self.todoist_note_deleted = TodoistSyncSignal('todoist_note_deleted', models.Note)

    def __getitem__(self, item):
        """
        :rtype: Signal
        """
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError('Signal %r not found' % item)
