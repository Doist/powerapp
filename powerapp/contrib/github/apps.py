# -*- coding: utf-8 -*-
"""
An extremely useful service to boost your morale. It adds notes with kittens
to every task you create. Works only for premium accounts.
"""
from powerapp.core.apps import ServiceAppConfig


class AppConfig(ServiceAppConfig):
    name = 'powerapp.contrib.github'
    verbose_name = 'Github Integration'
    url = 'http://todoist.com'
    description = __doc__
    models_module = None
