# -*- coding: utf-8 -*-
from . import utils
from celery.exceptions import SoftTimeLimitExceeded
from requests import HTTPError
from powerapp.celery_local import app
from powerapp.contrib.gcal_sync.utils import get_authorized_client, json_post
from powerapp.core.models.integration import Integration
from powerapp.core.models.user import User
from powerapp.core.logging_utils import ctx
from logging import getLogger


logger = getLogger(__name__)


@app.task(ignore_result=True)
def create_calendar(integration_id):
    try:
        integration = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        return
    with ctx(user=integration.user, integration=integration):
        calendar = utils.get_or_create_todoist_calendar(integration)
        utils.subscribe_to_todoist_calendar(integration, calendar)


@app.task(ignore_result=True)
def sync_gcal(integration_id):
    try:
        integration = Integration.objects.select_related('user').get(id=integration_id)
    except Integration.DoesNotExist:
        return
    with ctx(user=integration.user, integration=integration):
        try:
            utils.sync_gcal(integration)
        except SoftTimeLimitExceeded:
            logger.error('Synchronization with GCal took too long and was aborted')


@app.task(ignore_result=True)
def stop_channel(user_id, channel_id, resource_id):
    """
    Stop channel if integration does not exist
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    with ctx(user=user):
        client = get_authorized_client(user)
        try:
            json_post(client, '/channels/stop', id=channel_id, resouceId=resource_id)
        except HTTPError:
            # FIXME: it doesn't work :/
            pass
