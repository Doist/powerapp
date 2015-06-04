# -*- coding: utf-8 -*-
from . import utils
from requests import HTTPError
from powerapp.celery import app
from powerapp.contrib.gcal_sync.utils import get_authorized_client, json_post
from powerapp.core.models.integration import Integration
from powerapp.core.models.user import User


@app.task(ignore_result=True)
def sync_gcal(integration_id):
    try:
        integration = Integration.objects.get(id=integration_id)
    except Integration.DoesNotExist:
        return

    utils.sync_gcal(integration)


@app.task(ignore_result=True)
def stop_channel(user_id, channel_id, resource_id):
    """
    Stop channel if integration does not exist
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    client = get_authorized_client(user)
    try:
        json_post(client, '/channels/stop', id=channel_id, resouceId=resource_id)
    except HTTPError:
        # FIXME: it doesn't work :/
        pass
