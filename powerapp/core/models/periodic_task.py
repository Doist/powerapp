# -*- coding: utf-8 -*-
from django.db import models
from django.utils.timezone import now
from powerapp.core.models.service import logger


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

        # 2. run the task itself, as being asked
        logger.debug('Run periodic task %r', self.name)
        task_fun.func(self.integration, self.integration.user)

        # 3. update the database
        self.next_run = now() + task_fun.delta
        self.save()
