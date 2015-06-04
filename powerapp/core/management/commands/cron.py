# -*- coding: utf-8 -*-
from collections import namedtuple
import multiprocessing
import time
from logging import getLogger
import optparse

from django.db import connection
from django.utils.timezone import now
from django.conf import settings
from django.core.management.base import NoArgsCommand
from powerapp.core.models import Integration
from powerapp.core import periodic_tasks


logger = getLogger(__name__)


cron_task = namedtuple('cron_task', ['callable', 'kwargs', 'log_string'])


class Command(NoArgsCommand):

    option_list = list(NoArgsCommand.option_list) + [
        optparse.Option('-c', '--concurrency', type=int, default=None,
                        help='Concurrency level (number of processes handling '
                             'periodic jobs)'),
        optparse.Option('--loop', action='store_true', dest='loop',
                        help='If this flag is set, cron tasks will be executed '
                             'in a loop, with a minute interval')
    ]

    def handle_noargs(self, concurrency=None, loop=False, **options):
        while True:
            logger.debug('Cron: start')
            tasks = self.get_sync_tasks() + self.get_cron_tasks()

            # run task sequentially or in parallel
            if concurrency == 1:
                for task in tasks:
                    logger.debug('Cron: run "%s"', task.log_string)
                    task.callable(**task.kwargs)
            else:
                connection.close()
                pool = multiprocessing.Pool(processes=concurrency)
                for task in tasks:
                    logger.debug('Cron: run "%s"', task.log_string)
                    pool.apply_async(task.callable, kwds=task.kwargs)
                pool.close()
                pool.join()

            if not loop:
                break
            delay = 5 if settings.DEBUG else 60
            logger.debug('Cron: sleep for %s seconds', delay)
            time.sleep(delay)
        logger.debug('Cron: stop')

    def get_sync_tasks(self):
        # we return the list (not iterator or queryset) because we have to
        # close the connection immediately before we start pushing tasks to
        # the pool
        kwargs = {'resource_types': ['projects', 'items', 'notes']}
        ret = []
        for i in Integration.objects.filter(service_enabled=True,
                                            stateless=False,
                                            api_next_sync__lte=now()):
            ret.append(cron_task(i.api.sync, kwargs, '%s.api.sync()' % i))
        return ret

    def get_cron_tasks(self):
        # same thing with iterator -> list here
        tasks = periodic_tasks.get_pending()
        ret = []
        for task in tasks:
            ret.append(cron_task(task.run, {}, '%s.run()' % task))
        return ret
