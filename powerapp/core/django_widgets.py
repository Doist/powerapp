# -*- coding: utf-8 -*-
from itertools import chain
from django.forms.widgets import Select, Widget
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe


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


class SwitchWidget(Widget):

    choices = []

    def value_from_datadict(self, data, files, name):
        return data.getlist(name, None)

    def render(self, name, value, attrs=None):
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
