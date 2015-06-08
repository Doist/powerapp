# -*- coding: utf-8 -*-
from logging import getLogger
from django.db import models
from django.utils.timezone import now
from powerapp.core.logging_utils import ctx


logger = getLogger(__name__)


class PeriodicTask(models.Model):
    name = models.CharField(max_length=1024)
    integration = models.ForeignKey('Integration', db_index=True)
    next_run = models.DateTimeField(db_index=True)

    class Meta:
        app_label = 'core'
        unique_together = [('integration', 'name')]

    def __str__(self):
        return self.name

    def schedule_forward(self):
        task_fun = self.get_task_fun()
        if not task_fun:
            self.delete()
            return

        self.next_run = now() + task_fun.delta
        self.save()

    def run(self):
        # find the task function object
        task_fun = self.get_task_fun()
        if not task_fun:
            # unknown periodic task, destroy itself
            self.delete()
            return

        with ctx(user=self.integration.user, integration=self.integration):
            # 2. run the task as being asked
            logger.debug('Run periodic task %r', self.name)
            task_fun.func(self.integration)

    def get_task_fun(self):
        """
        Helper function returning PeriodicTaskFun object, associated with
        this task. Return None if nothing is found.
        """
        app_config = self.integration.service.app_config
        try:
            return app_config.periodic_tasks[self.name]
        except KeyError:
            pass
