# -*- coding: utf-8 -*-
from django.forms.fields import TypedChoiceField
from django.utils.encoding import force_text
from powerapp.core.django_widgets import ProjectsSelect


class ProjectChoiceField(TypedChoiceField):

    widget = ProjectsSelect

    def __init__(self, *args, **kwargs):
        kwargs['coerce'] = int
        super(ProjectChoiceField, self).__init__(*args, **kwargs)

    def valid_value(self, value):
        text_value = force_text(value)
        for project in self.choices:
            if text_value == force_text(project['id']):
                return True
        return False

    def populate_with_user(self, user):
        user.api.projects.sync()
        self.choices = user.api.projects.all()
