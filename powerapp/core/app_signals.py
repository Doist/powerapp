# -*- coding: utf-8 -*-
import traceback
from django.dispatch import Signal
from logging import getLogger


logger = getLogger(__name__)


class TodoistSyncSignal(Signal):

    SYNC_SIGNAL_ARGS = ['integration', 'obj']

    def __init__(self, name):
        super(TodoistSyncSignal, self).__init__(providing_args=self.SYNC_SIGNAL_ARGS)
        self.name = name

    def fire(self, integration, obj):
        """
        A wrapper around `send_robust` (with logging)
        """
        if self.has_listeners():
            logger.debug('Fire %s(%r, %r)' % (self.name,
                                              integration.user.email,
                                              obj['id']))
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
        self.todoist_project_added = TodoistSyncSignal('todoist_project_added')
        self.todoist_project_updated = TodoistSyncSignal('todoist_project_updated')
        self.todoist_project_deleted = TodoistSyncSignal('todoist_project_deleted')

        self.todoist_task_added = TodoistSyncSignal('todoist_task_added')
        self.todoist_task_updated = TodoistSyncSignal('todoist_task_updated')
        self.todoist_task_deleted = TodoistSyncSignal('todoist_task_deleted')

        self.todoist_note_added = TodoistSyncSignal('todoist_note_added')
        self.todoist_note_updated = TodoistSyncSignal('todoist_note_updated')
        self.todoist_note_deleted = TodoistSyncSignal('todoist_note_deleted')

    def __getitem__(self, item):
        """
        :rtype: Signal
        """
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError('Signal %r not found' % item)
