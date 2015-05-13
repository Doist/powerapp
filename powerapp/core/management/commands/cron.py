# -*- coding: utf-8 -*-
import multiprocessing
import time
from itertools import chain
from logging import getLogger
import optparse

from django.db import connection
from django.utils.timezone import now
from django.conf import settings
from django.core.management.base import NoArgsCommand
from powerapp.core.models.user import User
from powerapp.core import periodic_tasks


logger = getLogger(__name__)


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

            connection.close()
            pool = multiprocessing.Pool(processes=concurrency)
            for task, kwargs in tasks:
                logger.debug('Cron: run %s%r', str(task), kwargs)
                pool.apply_async(task, kwds=kwargs)
            pool.close()
            pool.join()
            if not loop:
                break
            delay = 5 if settings.DEBUG else 60
            logger.debug('Cron: sleep for %s seconds', delay)
            time.sleep(delay)
        logger.debug('Cron: stop')

    def get_sync_tasks(self):
        # we return the list (not iterator or whatever) because we have to
        # close the connection immediately before we start pushing tasks to
        # the pool
        kwargs = {'resource_types': ['projects', 'items', 'notes']}
        users = list(User.objects.filter(api_next_sync__lte=now()))
        return [(user.api.sync, kwargs) for user in users]

    def get_cron_tasks(self):
        # same thing with iterator -> list here
        tasks = list(periodic_tasks.get_pending())
        return [(task.run, {}) for task in tasks]
