# -*- coding: utf-8 -*-
import requests
import json
from logging import getLogger
from .apps import AppConfig
from django.dispatch.dispatcher import receiver
from .models import GithubDataMap
from powerapp.core.models.oauth import OAuthToken
from .views import ACCESS_TOKEN_CLIENT

logger = getLogger(__name__)


@receiver(AppConfig.signals.todoist_task_updated)
def on_task_changed(sender, user=None, service=None, integration=None, obj=None, **kwargs):
    try:
        item_issue_record = GithubDataMap.objects.get(integration=integration,
                                                      todoist_task_id=obj['id'])

        if obj.data.get("checked"):
            access_token = OAuthToken.objects.get(user=integration.user, client=ACCESS_TOKEN_CLIENT)

            resp = requests.patch(item_issue_record.github_data_url,
                                  params={'access_token': access_token.access_token},
                                  json={'state': "closed"},
                                  headers={'Accept': 'application/json'})

            if resp.status_code != 200:
                # TODO: LOG THE ERROR
                print(resp.json())
            else:
                item_issue_record.delete()

    except GithubDataMap.DoesNotExist:
        pass
