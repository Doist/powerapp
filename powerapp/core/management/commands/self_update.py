# -*- coding: utf-8 -*-
"""
A management command which is mostly useful on Heroku installations.
It checks environment variables and its current state and update
itself accordingly.

Duplicate the work of pre-compile and post-compile hooks mostly
"""
from django.core.management.base import NoArgsCommand
from powerapp.devops_utils import install_requirements, run_bootstrap_management_commands


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        install_requirements()
        run_bootstrap_management_commands()
