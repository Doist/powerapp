# -*- coding: utf-8 -*-
"""
Todoist-related utils
"""
import re
from collections import namedtuple
from powerapp.core.sync import UserTodoistAPI
from logging import getLogger


logger = getLogger(__name__)


def get_personal_project(integration, project_name, pid_field='project_id'):
    """
    It's a common thing for integrations to have personal projects, which they
    operate in.

    This helper function searches for a "personal project id" saved in the
    integration. If project is found and exist, it returns it. Otherwise
    it creates a new project with a given name, saves its id in the integration
    settings, and returns the object
    """
    # we're using the "shared API", because in a stateless mode we don't
    # have access to all user projects
    api = integration.user.api
    assert isinstance(api, UserTodoistAPI)  # IDE hint

    settings = integration.settings or {}

    # Try to find a project by id
    project_id = settings.get(pid_field)
    if project_id:
        project = api.projects.get_by_id(project_id)
        if project:
            return project

    # Project is not found. Search by project name, or create a new one
    projects = api.projects.all(filt=lambda p: p['name'] == project_name)
    project = projects[0] if projects else api.projects.add(project_name)

    # commit all changes and update settings
    api.commit()
    integration.update_settings(**{pid_field: project['id']})
    return project


url = namedtuple('url', ['link', 'title'])
re_url = re.compile(r'''
    (?P<link>https?://[^ \(\)]+) # URL itself
    \s*                  # optional space
    (?:\((?P<title>[^)]+)\))?       # optional text (in)
''', re.VERBOSE)


def extract_urls(text):
    """
    This function returns the list of URLs from the text

    Every item is returned as an URL object with link and optional title
    attribute
    """
    ret = []
    for m in re_url.finditer(text):
        ret.append(url(m.group('link'), m.group('title')))
    return ret


def plaintext_content(content, cut_url_pattern=None):
    """
    We expect the content of a task to be written in different formats. With
    this function we extract only the plaintext content
    """
    ret = []
    for chunk in re_url.split(content):
        if not chunk:
            continue

        if cut_url_pattern and cut_url_pattern in chunk:
            if chunk.startswith('http:') or chunk.startswith('https:'):
                continue

        ret.append(chunk.strip('() '))
    ret = ' '.join(ret)
    logger.debug('Plaintext content from %s -> %s (exclude links: %s)', content, ret, cut_url_pattern)
    return ret
