# -*- coding: utf-8 -*-
"""
Template tags to render forms with Materialize CSS: http://materializecss.com/forms.html
"""
from django import template

register = template.Library()


@register.inclusion_tag('materialize/form.html')
def materialize_form(form):
    """
    Take the form object and return its "materialized representation"
    """
    return {'form': form}
