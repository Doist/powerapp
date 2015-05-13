# -*- coding: utf-8 -*-
"""
An extremely useful service to boost your morale. It adds notes with kittens
to every task you create. Works only for premium accounts.
"""
from powerapp.core.apps import ServiceAppConfig


class AppConfig(ServiceAppConfig):
    name = 'powerapp.contrib.catcomments'
    verbose_name = 'Cat comments'
    url = 'http://thecatapi.com/'
    description = __doc__
    models_module = None
