# -*- coding: utf-8 -*-
"""
Google Calendar utility functions
"""
import json
import uuid
from logging import getLogger
from django.core.urlresolvers import reverse
from django.utils.crypto import salted_hmac
from powerapp.core import oauth
from . import oauth_impl
from powerapp.core.web_utils import ensure_https

logger = getLogger(__name__)
CALENDAR_SUMMARY = 'Todoist'
WEBHOOK_HMAC_SALT = 'gcal-webhooks'


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
    token = salted_hmac(WEBHOOK_HMAC_SALT, channel_id).hexdigest()
    resp = json_post(client, '/calendars/%s/events/watch' % calendar['id'],
                     id=channel_id, type='web_hook', address=webhook_url, token=token)
    integration.update_settings(channel_id=channel_id)
    logger.debug('Create cal. channel %s. Server replied %s', channel_id, resp)
    return channel_id


def sync_gcal(integration):
    """
    Sync Google Calendars with Todoist
    """
    logger.warning('TODO')


def json_get(client, url):
    return client.get('https://www.googleapis.com/calendar/v3' + url).json()


def json_post(client, url, **data):
    headers = {'Content-type': 'application/json'}
    return client.post('https://www.googleapis.com/calendar/v3' + url,
                       data=json.dumps(data),
                       headers=headers).json()

