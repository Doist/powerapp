# -*- coding: utf-8 -*-
"""
Evernote utility functions
"""
import pytz
from evernote.api.client import EvernoteClient
from django.conf import settings
from django.dispatch import Signal
from django.utils.html import escape
from evernote.edam.notestore.ttypes import SyncChunkFilter
from powerapp.contrib.evernote_sync.models import EvernoteSyncState, \
    EvernoteAccountCache
from powerapp.core.exceptions import PowerAppInvalidTokenError
from powerapp.core.models.oauth import OAuthToken
from powerapp.core.redis_utils import get_redis

evernote_note_changed = Signal(providing_args=['integration', 'note'])
evernote_note_deleted = Signal(providing_args=['integration', 'guid'])


ACCESS_TOKEN_CLIENT = 'evernote_sync'


def get_unauthorized_evernote_client():
    return EvernoteClient(sandbox=settings.EVERNOTE_SANDBOX,
                          consumer_key=settings.EVERNOTE_CONSUMER_KEY,
                          consumer_secret=settings.EVERNOTE_CONSUMER_SECRET)


def get_evernote_client(user):
    """
    Return the authenticated version of the Evernote client
    """
    try:
        token = OAuthToken.objects.get(user=user, client=ACCESS_TOKEN_CLIENT)
    except OAuthToken.DoesNotExist:
        raise PowerAppInvalidTokenError()
    return EvernoteClient(token=token.access_token, sandbox=settings.EVERNOTE_SANDBOX)


def get_notebooks(user):
    """
    Returns the list of notebooks.
    """
    cache = get_evernote_account_cache(user)
    cache.refresh()
    return cache.notebooks


def get_evernote_timezone(user):
    """
    Return a pytz timezone object from user's Evernote settings
    """
    cache = get_evernote_account_cache(user)
    cache.refresh()
    return pytz.timezone(cache.user_data.timezone)


def get_note_url(note):
    """
    Return evernote note URL by its guid

    The URL can be constructed according to
    https://dev.evernote.com/doc/articles/note_links.php, like
    https://[service]/shard/[shardId]/nl/[userId]/[noteGuid]/ , but we prefer
    to have more user-friendly URLs like
    https://[service]/Home.action?#b=[notebookGuid]&st=p&n=[noteGuid]
    """
    client = get_unauthorized_evernote_client()
    return 'https://%s/Home.action?#b=%s&st=p&n=%s' % (
        client.service_host, note.notebookGuid, note.guid,
    )


def get_evernote_account_cache(user):
    """
    Get or create the evernote account cache
    """
    obj, created = EvernoteAccountCache.objects.get_or_create(user=user)
    return obj


def format_note_content(content):
    return """<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
    <en-note>%s</en-note>
    """ % escape(content)


def sync_evernote(integration):
    """
    Sync evernote project with Todoist

    The function asks for new changes in Evernote account and generates
    `evernote_note_changed` and `evernote_note_deleted` events (handled in
    signals.py). It keeps the "last sync" state in the EvernoteSyncState object
    """
    lock_key = 'utils-sync-evernote-%s' % integration.id
    lock_timeout = 5 * 60
    blocking_timeout = 60

    with get_redis().lock(lock_key, timeout=lock_timeout,
                          blocking_timeout=blocking_timeout):
        local_sync_state, _ = EvernoteSyncState.objects.get_or_create(integration=integration)

        last_update_count, last_sync_time = _do_sync(integration,
                                                     local_sync_state.last_update_count,
                                                     local_sync_state.last_sync_time)

        local_sync_state.last_update_count = last_update_count
        local_sync_state.last_sync_time = last_sync_time
        local_sync_state.save()


def sync_evernote_projects(integration, notebook_guids):
    """
    Sync evernote projects by guids. The function is called whenever a user
    new projects to synchronization.

    We perform the synchronization "from scratch" and never save the updated
    value for last_update_count and last_sync_time
    """
    _do_sync(integration, 0, 0, notebook_guids)


def _do_sync(integration, last_update_count, last_sync_time, notebook_guids=None):
    """
    Low-level funtion performing sync operations. If notebook_guids is not None,
    launch note_add events only for notebooks with given guids

    Returns new values for last_update_count and last_sync_time
    """
    client = get_evernote_client(integration.user)
    note_store = client.get_note_store()
    sync_state = note_store.getSyncState()

    if notebook_guids is not None:
        notebook_guids = set(notebook_guids)

    # nothing to update?
    if last_update_count == sync_state.updateCount:
        return last_update_count, last_sync_time

    # do we need a full sync?
    if sync_state.fullSyncBefore > last_sync_time:
        last_update_count = 0

    max_entries = 1000

    sync_filter = SyncChunkFilter()
    sync_filter.includeNotes = True
    sync_filter.includeNoteAttributes = True
    sync_filter.includeNotebooks = True
    sync_filter.includeExpunged = True

    while True:
        chunk = note_store.getFilteredSyncChunk(last_update_count,
                                                max_entries,
                                                sync_filter)

        for note in (chunk.notes or []):
            if notebook_guids is None or note.notebookGuid in notebook_guids:
                if note.deleted is not None:
                    evernote_note_deleted.send(None, integration=integration, guid=note.guid)
                else:
                    evernote_note_changed.send(None, integration=integration, note=note)

        for guid in (chunk.expungedNotes or []):
            evernote_note_deleted.send(None, integration=integration, guid=guid)

        last_update_count = chunk.chunkHighUSN
        last_sync_time = chunk.currentTime

        if chunk.chunkHighUSN == chunk.updateCount:
            return last_update_count, last_sync_time
