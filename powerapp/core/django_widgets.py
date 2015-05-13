# -*- coding: utf-8 -*-
from itertools import chain
from django.forms.widgets import Select
from django.utils.encoding import force_text


class ProjectsSelect(Select):

    def render_options(self, choices, selected_choices):
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []

        sort_key = lambda p: (p['item_order'], p['id'])
        for project in sorted(chain(self.choices, choices), key=sort_key):
            option_value = force_text(project['id'])
            indent = max(project['indent'] - 1, 0)
            option_label = '..' * indent + ' ' + project['name']
            output.append(self.render_option(selected_choices, option_value, option_label))
        return '\n'.join(output)
