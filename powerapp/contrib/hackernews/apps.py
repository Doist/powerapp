# -*- coding: utf-8 -*-
"""
Pools the hackernews feed and add tasks with links to new posts to your Todoist
project.
"""
from powerapp.core.apps import ServiceAppConfig


class AppConfig(ServiceAppConfig):
    name = 'powerapp.contrib.hackernews'
    verbose_name = 'Hacker News Reader'
    url = 'http://news.ycombinator.com'
    description = __doc__
    models_module = None
