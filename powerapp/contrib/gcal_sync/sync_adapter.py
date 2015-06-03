# -*- coding: utf-8 -*-
from logging import getLogger
import pytz
import uuid
import re
import datetime
from requests import HTTPError
from pyrfc3339.parser import parse as parse_date
from pyrfc3339.generator import generate as generate_date
from powerapp.core.todoist_utils import plaintext_content
from powerapp.sync_bridge.bridge import SyncAdapter, SyncBridge, task, undefined
from powerapp.sync_bridge.models import ItemMapping
from powerapp.sync_bridge.todoist_sync_adapter import TodoistSyncAdapter


from . import utils


logger = getLogger(__name__)


def build_bridge(integration, project_id):
    td = TodoistSyncAdapter(project_id)
    gc = GcalSyncAdapter()
    return SyncBridge(integration, td, gc)


def get_bridge_by_event_id(integration, event_id):
    """
    Return SyncBridge instance by event_id. We fall back to Inbox if cannot
    find a mapping

    Note that here we rely on the fact that the bridge has a predictable
    structure (todoist <--> gcal) and sides of the bridge have predictable
    names containing id of the project and the guid of the notebook coresondingly
    """

    mapping = ItemMapping.objects.filter(right_id=event_id, integration=integration).order_by('-id').first()
    if mapping:
        match = re.compile(r'^todoist-(\d+)-gcal$').match(mapping.bridge_name)
        if match:
            return build_bridge(integration, match.group(1))

    inbox_project = integration.user.get_inbox_project()
    return build_bridge(integration, inbox_project)


class GcalSyncAdapter(SyncAdapter):
    """
    Sync Adapter for Google calendar
    """
    DEFAULT_NAME = 'gcal'
    ESSENTIAL_FIELDS = ['content', 'due_date', 'date_string']

    def __init__(self):
        super(GcalSyncAdapter, self).__init__(name=self.DEFAULT_NAME)

    def get_calendar_id(self):
        return self.bridge.integration.settings['calendar_id']

    def push_task(self, task_id, task, extra):
        """
        Push task from Todoist to Google Calendar and save extra information in the
        "extra" field
        """
        user = self.bridge.integration.user
        client = utils.get_authorized_client(user)

        if not task.due_date or task.due_date.second == 59:
            # ignore this task or try to delete it
            if task_id:
                self.delete_task(task_id, extra)
            return None, None

        orig_event = None
        create = True

        # try to get orig event
        if task_id:
            try:
                orig_event = utils.json_get(client, '/calendars/%s/events/%s' % (self.get_calendar_id(), task_id))
                create = False
            except HTTPError:
                pass

        if create:
            task_id = uuid.uuid4().hex

        event_duration = get_event_duration(orig_event)
        event_content = plaintext_content(task.content, 'google.com/calendar')
        attrs = {
            'summary': event_content,
            'start': {
                'dateTime': generate_date(task.due_date, accept_naive=True),
            },
            'end': {
                'dateTime': generate_date(task.due_date + event_duration, accept_naive=True),
            }
        }
        if create:
            attrs['id'] = task_id

        if create:
            command = utils.json_post
            url = '/calendars/%s/events' % self.get_calendar_id()
        else:
            command = utils.json_put
            url = '/calendars/%s/events/%s' % (self.get_calendar_id(), task_id)
        resp = command(client, url, **attrs)
        logger.debug('Create or update a task on %s. '
                     'Data: %s. Server replied: %s', url, attrs, resp)
        new_extra = {
            'original_content': task.content,
            'original_due_date': task.due_date,
            'original_date_string': task.date_string,
        }
        return task_id, new_extra

    def delete_task(self, task_id, extra):
        """
        Delete calendar event by id
        """
        client = utils.get_authorized_client(self.bridge.integration.user)
        url = '/calendars/%s/events/%s' % (self.get_calendar_id(), task_id)
        utils.json_delete(client, url)

    def task_from_data(self, data, extra):
        """
        We sync back only due_date and date_string.
        """
        try:
            gcal_due_date = parse_date(data['start']['dateTime'])
        except ValueError:
            # an event without a due date (whole day event maybe). Skip
            return

        # if the task is new, we should fill in the content
        if not extra:
            plaintext_content = data.get('summary') or 'Google Calendar event'
            backlink = data['htmlLink']
            content = '%s (%s)' % (backlink, plaintext_content)
        else:
            content = undefined

        # sync due date and date string, but
        # don't overwrite "Todoist rich date strings"
        due_date_utc = gcal_due_date.astimezone(pytz.utc)
        user_timezone = self.bridge.integration.user.get_timezone()
        local_due_date = gcal_due_date.astimezone(user_timezone)
        date_string = local_due_date.strftime('%d %b %Y at %H:%M')

        original_due_date = extra.get('original_due_date')
        if due_date_utc.replace(tzinfo=None) == original_due_date:
            logger.debug('Due date was not changed. Don\'t update the date')
            due_date_utc = undefined
            date_string = undefined
        else:
            logger.debug('Due date changed from %s to %s. Update the date' % (original_due_date, due_date_utc))

        return task(content=content,
                    due_date=due_date_utc,
                    date_string=date_string)


def get_event_duration(event, default=datetime.timedelta(hours=1)):
    """
    Return the duration of the event (as a timedelta object)
    """
    if event is None:
        return default

    try:
        start = parse_date(event['start']['dateTime'])
        end = parse_date(event['start']['endTime'])
    except (KeyError, ValueError):
        return default

    if end < start:
        return default

    return end - start
