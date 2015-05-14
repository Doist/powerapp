# -*- coding: utf-8 -*-
"""
A management command which is mostly useful on Heroku installations.
It checks environment variables and its current state and update
itself accordingly.

Duplicate the work of pre-compile and post-compile hooks mostly
"""
import os
import re
import subprocess
from logging import getLogger
from django.core.management import call_command
from django.core.management.base import NoArgsCommand


logger = getLogger(__name__)


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        install_requirements()
        run_management_commands()


def install_requirements():
    services = os.environ.get('POWERAPP_SERVICES')
    for service in re.split(r'[\s,;]+', services or ''):
        if not service:
            continue
        if '/' in service:
            args = ['-e', service]
        else:
            args = [service]
        logger.debug('Installing with pip: %r', args)
        subprocess.call(['pip', 'install'] + args)


def run_management_commands():
    logger.debug('Calling ./manage.py migrate')
    call_command('migrate')
    logger.debug('Calling ./manage.py collectstatic')
    call_command('collectstatic', interactive=False)
    logger.debug('Calling ./manage.py collect_services')
    call_command('collect_services')
