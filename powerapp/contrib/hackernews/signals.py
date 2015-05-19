# -*- coding: utf-8 -*-
import requests
import feedparser
import time
import datetime
from logging import getLogger
from django.conf import settings

from .apps import AppConfig
from powerapp.core.sync import StatelessTodoistAPI
from powerapp.core.todoist_utils import get_personal_project, extract_urls


logger = getLogger(__name__)


DEFAULT_FEED_URL = 'https://news.ycombinator.com/rss'
PROJECT_NAME = 'HackerNews feed'


@AppConfig.periodic_task(datetime.timedelta(minutes=1 if settings.DEBUG else 15))
def poll_hackernews_rss_feed(integration):
    assert isinstance(integration.api, StatelessTodoistAPI)  # IDE hint

    settings = integration.settings
    if not isinstance(settings, dict):
        settings = {}

    project = get_personal_project(integration, PROJECT_NAME)
    resp = requests.get(integration.settings.get('feed_url', DEFAULT_FEED_URL)).content
    feed = feedparser.parse(resp)

    with integration.api.autocommit():
        for entry in feed.entries:
            if 'published_parsed' in entry:
                published = int(time.mktime(entry.published_parsed))
                if published < settings.get('last_updated', 0):
                    continue

            content = u'%s (%s)' % (entry.link, entry.title)
            logger.debug('Added hacker news %s' % content)
            integration.api.items.add(content, project['id'])

    integration.update_settings(last_updated=int(time.time()),
                                project_id=project['id'])
