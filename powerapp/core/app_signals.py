# -*- coding: utf-8 -*-
import traceback
from django.dispatch import Signal
from logging import getLogger
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
            logger.debug('Fire %s(%r, %r)' % (self.name,
                                              integration.user.email,
                                              obj['id']))

            # type conversion
            if not isinstance(obj, self.model):
                obj = self.model(obj, integration.api)

            resp = self.send_robust(None, integration=integration, obj=obj)
            for func, item in resp:
                if hasattr(item, '__traceback__'):
                    logger.error('%s() -> %s', func.__name__, item)
                    tb_lines = traceback.format_tb(item.__traceback__)
                    logger.error(''.join(tb_lines))
                else:
                    logger.debug('%s() -> %s', func.__name__, item)


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
