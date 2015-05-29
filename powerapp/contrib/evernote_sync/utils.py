# -*- coding: utf-8 -*-
"""
Evernote utility functions
"""
import datetime
from evernote.api.client import EvernoteClient
from django.conf import settings
from django.utils.timezone import now
from django.utils.html import escape


from .models import EvernoteCache


# See https://sandbox.evernote.com/api/DeveloperToken.action
DEVELOPER_TOKEN = 'S=s1:U=90e9d:E=154f7120952:C=14d9f60dd38:P=1cd:A=en-devtoken:V=2:H=c427b7991dfe7210652a47d3bd75ff0a'
UPDATE_THRESHOLD = datetime.timedelta(seconds=30) if settings.DEBUG else datetime.timedelta(minutes=15)


def get_evernote_client(user):
    """
    Return the authenticated version of the Evernote client
    """
    return EvernoteClient(token=DEVELOPER_TOKEN, sandbox=True)


def get_notebooks(user):
    """
    Returns the list of notebooks.
    """
    cache = get_evernote_cache(user)
    refresh_evernote_cache(user, cache)
    return cache.notebooks


def get_evernote_cache(user):
    obj, created = EvernoteCache.objects.get_or_create(user=user)
    return obj


def refresh_evernote_cache(user, cache):
    """
    Refresh the evernote cache if required
    """
    if cache.last_update_time > now() - UPDATE_THRESHOLD:
        # no need to update yet
        return

    # let's see if there are some updates
    client = get_evernote_client(user)
    note_store = client.get_note_store()
    update_count = note_store.getSyncState().updateCount
    if update_count <= cache.last_update_count:
        cache.last_update_time = now()
        cache.save()
        return

    # it's time for update
    cache.notebooks = note_store.listNotebooks()
    cache.last_update_time = now()
    cache.last_update_count = update_count
    cache.save()

def format_note_content(content):
    return """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
    <en-note>%s</en-note>
    """ % escape(content)
