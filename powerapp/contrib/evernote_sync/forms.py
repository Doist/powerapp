# -*- coding: utf-8 -*-
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from powerapp.core import django_forms

from . import utils

DEFAULT_PROJECT_NAME = u'Evernote'


class SwitchWidget(forms.Widget):

    choices = []

    def value_from_datadict(self, data, files, name):
        return data.getlist(name, None)

    def render(self, name, value, attrs=None):
        print(name, value)
        checked_options = set(value or [])
        ret = []
        for value, label in self.choices:
            ret.append(self.render_checkbox(name, value, label,
                                            value in checked_options))
        return mark_safe('\n'.join(ret))

    @staticmethod
    def render_checkbox(name, value, label, checked):
        checked_str = mark_safe(' checked') if checked else ''
        return format_html(u'<p></p>'
                           u'<div class="switch">'
                           u'   <label>'
                           u'       <input type="checkbox" name="{}" value="{}"{}>'
                           u'       <span class="lever"></span>'
                           u'       {}'
                           u'   </label>'
                           u'</div>', name, value, checked_str, label)


class EvernoteChoiceField(forms.MultipleChoiceField):

    widget = SwitchWidget

    def populate_with_user(self, user):
        notebooks = utils.get_notebooks(user)
        self.choices = [(n.guid, n.name) for n in notebooks]



class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'evernote_sync'
    evernote_notebooks = EvernoteChoiceField(label=u'Evernote Notebook', required=False)

    def pre_save(self, integration_settings):
        """
        Create Todoist projects and map them to evernote notebooks
        """
        # a dict: project_id -> notebook guid
        projects_notebooks = integration_settings.get('projects_notebooks') or {}
        # inverted structure
        notebooks_projects = {v: k for k, v in projects_notebooks.items()}

        # a dict: notebook guid: notebook name
        notebooks = {n.guid: n.name for n in utils.get_notebooks(self.integration.user)}

        # create all projects we need to perform sync operations
        projects = []
        guids = []
        with self.integration.user.api.autocommit():
            for guid in integration_settings.get('evernote_notebooks'):
                # check that project exists
                project_id = notebooks_projects.get(guid)
                if project_id:
                    if not self.integration.user.api.projects.get_by_id(project_id):
                        project_id = None
                # if it doesn't exist, create one
                if project_id is None:
                    project_name = notebooks.get(guid, DEFAULT_PROJECT_NAME)
                    project = self.integration.user.api.projects.add(name=project_name)
                    projects.append(project)
                    guids.append(guid)

        # populate "project_notebooks" with newer values
        # at this point all projects have to have valid ids
        pids = [p['id'] for p in projects]
        projects_notebooks.update(dict(zip(pids, guids)))
        integration_settings['projects_notebooks'] = projects_notebooks
        return integration_settings




