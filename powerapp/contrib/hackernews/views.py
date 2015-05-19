# -*- coding: utf-8 -*-
from django import forms
from django.utils.safestring import mark_safe
from powerapp.core import generic_views
from powerapp.core.django_forms import IntegrationForm


class HackerNewsForm(IntegrationForm):
    service_label = 'hackernews'
    feed_url = forms.CharField(label=u'RSS feed URL', required=True,
                               initial='https://news.ycombinator.com/rss',
                               help_text=mark_safe(u'Check out <a href="https://edavis.github.io/hnrss/" target="_blank">hnrss project</a> '
                                         u'for more powerful RSS filtration'))


class EditIntegrationView(generic_views.EditIntegrationView):
    form = HackerNewsForm
    service_label = 'hackernews'
