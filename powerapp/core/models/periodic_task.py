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

    def run(self):
        # 1. find itself in a service
        app_config = self.integration.service.app_config
        try:
            task_fun = app_config.periodic_tasks[self.name]
        except KeyError:
            # unknown periodic task
            return

        with ctx(user=self.integration.user, integration=self.integration):
            # 2. run the task itself, as being asked
            logger.debug('Run periodic task %r', self.name)
            task_fun.func(self.integration)

        # 3. update the database
        self.next_run = now() + task_fun.delta
        self.save()
