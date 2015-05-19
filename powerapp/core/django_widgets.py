# -*- coding: utf-8 -*-
from itertools import chain
from django.forms.widgets import Select
from django.utils.encoding import force_text


class ProjectsSelect(Select):

    def render_options(self, choices, selected_choices):
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []

        filter_func = lambda p: isinstance(p['id'], int)
        sort_key = lambda p: (p['item_order'], p['id'])

        projects = chain(self.choices, choices)
        projects = filter(filter_func, projects)
        projects = sorted(projects, key=sort_key)

        for project in projects:
            option_value = force_text(project['id'])
            indent = max(project['indent'] - 1, 0)
            option_label = '..' * indent + ' ' + project['name']
            output.append(self.render_option(selected_choices, option_value, option_label))
        return '\n'.join(output)
