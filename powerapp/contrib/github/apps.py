# -*- coding: utf-8 -*-
import environ
from powerapp.core.apps import ServiceAppConfig

env = environ.Env()

class AppConfig(ServiceAppConfig):
    name = 'powerapp.contrib.github'
    verbose_name = 'Github Integration'
    url = 'http://todoist.com'
    description = __doc__
    models_module = None

    GITHUB_CLIENT_ID = env('GITHUB_CLIENT_ID', default=None)
    GITHUB_CLIENT_SECRET = env('GITHUB_CLIENT_SECRET', default=None)
