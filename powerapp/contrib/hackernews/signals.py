# -*- coding: utf-8 -*-
import re
import requests
import feedparser
import time
import datetime
from logging import getLogger

from django.conf import settings

from .apps import AppConfig
from powerapp.core.sync import TodoistAPI
from powerapp.core.todoist_utils import get_personal_project, extract_urls


logger = getLogger(__name__)


FEED_URL = 'https://news.ycombinator.com/rss'
PROJECT_NAME = 'HackerNews feed'


@AppConfig.periodic_task(datetime.timedelta(minutes=1 if settings.DEBUG else 15))
def poll_hackernews_rss_feed(integration):
    assert isinstance(integration.api, TodoistAPI)  # IDE hint

    settings = integration.settings
    if not isinstance(settings, dict):
        settings = {}

    last_updated = settings.get('last_updated', 0)
    project = get_personal_project(integration, PROJECT_NAME)

    resp = requests.get(FEED_URL).content
    feed = feedparser.parse(resp)

    known_urls = get_urls(integration, project['id'])

    with integration.api.autocommit():
        for entry in feed.entries:

            # filter out by last update
            if 'published_parsed' in entry:
                published = int(time.mktime(entry.published_parsed))
                if published < last_updated:
                    continue
                else:
                    last_updated = published

            # filter out by currently known records
            if entry.link in known_urls:
                continue

            content = u'%s (%s)' % (entry.link, entry.title)
            integration.api.items.add(content, project['id'])

    integration.settings = dict(settings,
                                last_updated=last_updated,
                                project_id=project['id'])
    integration.save()


def get_urls(integration, project_id):
    urls = set()
    integration.api.items.sync()
    items = integration.api.items.all(lambda i: i['project_id'] == project_id)
    for item in items:
        for url in extract_urls(item['content']):
            urls.add(url)
    return urls
