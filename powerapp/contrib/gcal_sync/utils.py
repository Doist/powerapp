# -*- coding: utf-8 -*-
"""
Google Calendar utility functions
"""
import json
import uuid
from logging import getLogger
from django.core.urlresolvers import reverse
from django.dispatch.dispatcher import Signal
from django.utils.crypto import salted_hmac, constant_time_compare
from powerapp.core import oauth
from . import oauth_impl
from powerapp.core.exceptions import PowerAppError
from powerapp.core.web_utils import ensure_https
from django.utils.six.moves.urllib import parse


logger = getLogger(__name__)
CALENDAR_SUMMARY = 'Todoist'
WEBHOOK_HMAC_SALT = 'gcal-webhooks'


gcal_event_changed = Signal(providing_args=['integration', 'event'])
gcal_event_deleted = Signal(providing_args=['integration', 'event_id'])


def get_authorized_client(user):
    """
    Return the Authorized requests session object
    """
    client = oauth.get_client_by_name(oauth_impl.OAUTH_CLIENT_NAME)
    return client.get_oauth2_session(user)


def get_or_create_todoist_calendar(integration):
    client = get_authorized_client(integration.user)
    resp = json_get(client, '/users/me/calendarList')

    my_calendars = [c for c in resp['items'] if c['accessRole'] == 'owner']

    calendars_by_id = {c['id']: c for c in my_calendars}
    calendars_by_summary = {c['summary']: c for c in my_calendars}
    calendar_id = integration.settings.get('calendar_id')

    # find calendar by id
    if calendar_id and calendar_id in calendars_by_id.keys():
        calendar = calendars_by_id[calendar_id]
        logger.debug('Found existing calendar %r', calendar)

    # find and save calendar by summary
    elif CALENDAR_SUMMARY in calendars_by_summary:
        calendar = calendars_by_summary[CALENDAR_SUMMARY]
        integration.update_settings(calendar_id=calendar['id'])
        logger.debug('Found existing calendar by name: %r', calendar)

    # or just create a new one
    else:
        calendar = json_post(client, '/calendars', summary=CALENDAR_SUMMARY)
        integration.update_settings(calendar_id=calendar['id'])
        logger.debug('Created a new calendar: %r', calendar)

    return calendar


def subscribe_to_todoist_calendar(request, integration, calendar):
    """
    Subscribe for all events from the calendar

    See https://developers.google.com/google-apps/calendar/v3/push?hl=en_US for
    more details.
    """
    if 'channel_id' in integration.settings:
        channel_id = integration.settings['channel_id']
        logger.debug('We have cal. channel %s. Skip subscription', channel_id)
        return channel_id

    client = get_authorized_client(integration.user)
    channel_id = str(uuid.uuid4())
    webhook_url = ensure_https(request.build_absolute_uri(
        reverse('gcal_sync:accept_webhook', args=(integration.id, ))
    ))
    token = create_webhook_token(integration)
    resp = json_post(client, '/calendars/%s/events/watch' % calendar['id'],
                     id=channel_id, type='web_hook', address=webhook_url, token=token)
    integration.update_settings(channel_id=channel_id)
    logger.debug('Create cal. channel %s. Server replied %s', channel_id, resp)
    return channel_id


def create_webhook_token(integration):
    """
    Create a signed dict with integration_id (i) and user_id (u) attributes
    """
    qs = {'i': integration.id, 'u': integration.user_id}
    string = parse.urlencode(qs)
    token = salted_hmac(WEBHOOK_HMAC_SALT, string).hexdigest()
    return '%s?%s' % (token, string)


def validate_webhook_token(string):
    """
    Verifies the webhook token, andn raises "Invalid webhook token" exception,
    or return {u: <user_id>, i: <integration_id>} dict
    """
    token, qs = parse.splitquery(string)
    expected_token = salted_hmac(WEBHOOK_HMAC_SALT, qs or '').hexdigest()
    if not constant_time_compare(token, expected_token):
        raise PowerAppError('Invalid Webhook token')
    return dict(parse.parse_qsl(qs))


def sync_gcal(integration):
    """
    Sync Google Calendars with Todoist
    """
    sync_token = integration.settings.get('sync_token', '')
    page_token = ''
    calendar_id = integration.settings.get('calendar_id')
    url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events' % calendar_id
    client = get_authorized_client(integration.user)

    for _ in range(1000):   # instead of "while True:"
        params = {}
        if sync_token:
            params['syncToken'] = sync_token
        if page_token:
            params['pageToken'] = page_token

        resp = client.get(url, params=params)
        if resp.status_code == 410:
            sync_token = ''
            page_token = ''
            continue

        resp.raise_for_status()
        json_resp = resp.json()

        page_token = json_resp.get('nextPageToken')
        sync_token = json_resp.get('nextSyncToken')

        for gcal_event in json_resp['items']:
            if gcal_event['status'] == 'cancelled':
                gcal_event_deleted.send(None, integration=integration,
                                        event_id=gcal_event['id'])
            else:
                gcal_event_changed.send(None, integration=integration,
                                        event=gcal_event)

        if not page_token:
            integration.update_settings(sync_token=sync_token)
            return


def json_get(client, url, **params):
    resp = client.get('https://www.googleapis.com/calendar/v3' + url,
                      params=params)
    resp.raise_for_status()
    return resp.json()


def json_delete(client, url, **params):
    resp = client.delete('https://www.googleapis.com/calendar/v3' + url,
                         params=params).json()
    resp.raise_for_status()
    return resp.json()


def json_post(client, url, **data):
    headers = {'Content-type': 'application/json'}
    resp = client.post('https://www.googleapis.com/calendar/v3' + url,
                       data=json.dumps(data),
                       headers=headers)
    resp.raise_for_status()
    return resp.json()


def json_put(client, url, **data):
    headers = {'Content-type': 'application/json'}
    resp = client.put('https://www.googleapis.com/calendar/v3' + url,
                      data=json.dumps(data),
                      headers=headers)
    resp.raise_for_status()
    return resp.json()
