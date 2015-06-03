# -*- coding: utf-8 -*-
import json
from xml.etree import ElementTree
import requests
from logging import getLogger
from django.dispatch.dispatcher import receiver
from .apps import AppConfig
from powerapp.core.sync import StatelessTodoistAPI


logger = getLogger(__name__)


@receiver(AppConfig.signals.todoist_task_added)
def on_task_added(sender, integration=None, obj=None, **kwargs):
    """
    Add a comment with a random cat to every new task
    """
    if obj['project_id'] != integration.settings['project']:
        return

    assert isinstance(integration.api, StatelessTodoistAPI)  # IDE hint
    with integration.api.autocommit():
        url, source_url = get_cat_picture()
        content = '%s (The cat API)' % source_url
        integration.api.notes.add(obj['id'], content,
                           file_attachment=json.dumps({
                               'file_url': url,
                               'file_name': 'cat.jpg',
                               'file_type': 'image/jpeg',
                               'tn_l': [url, 500, 500],
                               'tn_m': [url, 500, 500],
                               'tn_s': [url, 500, 500],
                           }))


def get_cat_picture():
    resp = requests.get('http://thecatapi.com/api/images/get',
                        params={'format': 'xml',
                                'results_per_page': 1,
                                'size': 'med'})
    tree = ElementTree.fromstring(resp.content)
    url = tree.findtext('data/images/image[1]/url')
    source_url = tree.findtext('data/images/image[1]/source_url')
    return url, source_url
