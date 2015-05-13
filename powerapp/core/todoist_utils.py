# -*- coding: utf-8 -*-
"""
Todoist-related utils
"""
from collections import namedtuple
import re
from powerapp.core.sync import TodoistAPI


def get_personal_project(user, integration, project_name, pid_field='project_id'):
    """
    It's a common thing for integrations to have personal projects, which they
    operate in.

    This helper function searches for a "personal project id" saved in the
    integration. If project is found and exist, it returns it. Otherwise
    it creates a new project with a given name, saves its id in the integration
    settings, and returns the object
    """
    assert isinstance(user.api, TodoistAPI)  # IDE hint

    settings = integration.settings or {}

    # Try to find a project by id
    project_id = settings.get(pid_field)
    if project_id:
        project = user.api.projects.get_by_id(project_id)
        if project:
            return project

    # Project is not found. Search by project name, or create a new one
    user.api.projects.sync()
    projects = user.api.projects.all(filt=lambda p: p['name'] == project_name)
    project = projects[0] if projects else user.api.projects.add(project_name)

    # commit all changes and update settings
    user.api.commit()
    integration.update_settings(**{pid_field: project['id']})
    return project


url = namedtuple('url', ['link', 'title'])
re_url = re.compile(r'''
    (?P<link>https?://[^ \(\)]+) # URL itself
    \s*                  # optional space
    (\((?P<title>[^)]+)\))?       # optional text (in)
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
