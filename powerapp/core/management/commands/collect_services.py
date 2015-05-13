# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand

from powerapp.core import service_collector, periodic_tasks


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        service_collector.collect_services()
        periodic_tasks.sync()
