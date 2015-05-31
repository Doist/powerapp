# -*- coding: utf-8 -*-
"""
Evernote utility functions
"""
from evernote.api.client import EvernoteClient
from django.conf import settings
from django.dispatch import Signal
from django.utils.html import escape
from evernote.edam.notestore.ttypes import SyncChunkFilter
from powerapp.contrib.evernote_sync.models import EvernoteSyncState, \
    EvernoteAccountCache
from powerapp.core.models.oauth import AccessToken


# notebook_changed, notebook_deleted signals aren't used yet
evernote_notebook_changed = Signal(providing_args=['user', 'notebook'])
evernote_notebook_deleted = Signal(providing_args=['user', 'guid'])

evernote_note_changed = Signal(providing_args=['user', 'note'])
evernote_note_deleted = Signal(providing_args=['user', 'guid'])


ACCESS_TOKEN_CLIENT = 'evernote_sync'


def get_unauthorized_evernote_client():
    return EvernoteClient(sandbox=settings.EVERNOTE_SANDBOX,
                          consumer_key=settings.EVERNOTE_CONSUMER_KEY,
                          consumer_secret=settings.EVERNOTE_CONSUMER_SECRET)


def get_evernote_client(user):
    """
    Return the authenticated version of the Evernote client
    """
    access_token = AccessToken.objects.get(user=user, client=ACCESS_TOKEN_CLIENT)
    return EvernoteClient(token=access_token.token, sandbox=settings.EVERNOTE_SANDBOX)


def get_notebooks(user):
    """
    Returns the list of notebooks.
    """
    cache = get_evernote_account_cache(user)
    cache.refresh()
    return cache.notebooks


def get_note_url(user, guid):
    """
    Return evernote note URL by its guid

    The URL is constructed according to
    https://dev.evernote.com/doc/articles/note_links.php:

    https://[service]/shard/[shardId]/nl/[userId]/[noteGuid]/
    """
    client = get_evernote_client(user)
    account_cache = get_evernote_account_cache(user)
    account_cache.refresh()

    return 'https://%s/shard/%s/nl/%s/%s/' % (
        client.service_host,
        account_cache.user_data.shardId,
        account_cache.user_data.id,
        guid,
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
    client = get_evernote_client(integration.user)
    note_store = client.get_note_store()

    sync_state = note_store.getSyncState()
    local_sync_state, _ = EvernoteSyncState.objects.get_or_create(integration=integration)

    # nothing to update?
    if local_sync_state.last_update_count == sync_state.updateCount:
        return

    # do we need a full sync?
    if sync_state.fullSyncBefore > local_sync_state.last_sync_time:
        local_sync_state.last_update_count = 0

    max_entries = 1000

    sync_filter = SyncChunkFilter()
    sync_filter.includeNotes = True
    sync_filter.includeNoteAttributes = True
    sync_filter.includeNotebooks = True
    sync_filter.includeExpunged = True

    while True:
        chunk = note_store.getFilteredSyncChunk(local_sync_state.last_update_count, max_entries, sync_filter)

        if chunk.notebooks:
            for notebook in chunk.notebooks:
                evernote_notebook_changed.send(None, integration=integration, notebook=notebook)

        if chunk.expungedNotebooks:
            for guid in chunk.expungedNotebooks:
                evernote_notebook_deleted.send(None, integration=integration, guid=guid)

        if chunk.notes:
            for note in chunk.notes:
                if note.deleted is not None:
                    evernote_note_deleted.send(None, integration=integration, guid=note.guid)
                else:
                    evernote_note_changed.send(None, integration=integration, note=note)

        if chunk.expungedNotes:
            for guid in chunk.expungedNotes:
                evernote_note_deleted.send(None, integration=integration, guid=guid)

        local_sync_state.last_update_count = chunk.chunkHighUSN
        local_sync_state.last_sync_time = chunk.currentTime

        if chunk.chunkHighUSN == chunk.updateCount:
            local_sync_state.save()
            return
