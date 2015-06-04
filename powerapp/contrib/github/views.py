# -*- coding: utf-8 -*-
import json
import uuid
import hmac
from hashlib import sha1

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.encoding import force_text, force_bytes
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import Http404, HttpResponse
import django.forms

from powerapp.core import django_fields
from powerapp.core.models.integration import Integration
from powerapp.core.models import Service
from powerapp.core import django_forms, generic_views
from powerapp.core.models.oauth import OAuthToken
from powerapp.core.exceptions import PowerAppError
from powerapp.core.web_utils import extend_qs
from powerapp.core.sync import StatelessTodoistAPI
from .models import GithubItemIssueMap


GITHUB_AUTHORIZE_ENDPOINT = 'https://github.com/login/oauth/authorize'
GITHUB_ACCESS_TOKEN_ENDPOINT = 'https://github.com/login/oauth/access_token'


ACCESS_TOKEN_CLIENT = "github"
OAUTH_STATE_SESSION_KEY = "github_oauth_state"

SETTING_KEY_GITHUB_USER_ID = "github_user_id"
SETTING_KEY_WEBHOOK_SECRET = "webhook_secret"
SETTING_KEY_PROJECT = "project"


class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'github'
    project = django_fields.ProjectChoiceField(label=u'Project to github tasks to')
    webhook_secret = django.forms.fields.CharField(label="Webhook 'Secret' string", required=True)


class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'github'
    access_token_client = 'github'
    form = IntegrationForm

    def extra_template_context(self, request, integration):
        if not integration:
            return {}

        webhook_url = self.request.build_absolute_uri(
            reverse('github:webhook', kwargs={"integration_id": integration.id}))

        return {
            "webhook_url": webhook_url
        }

    def access_token_redirect(self, request):
        request.session['github_auth_redirect'] = request.path
        return redirect('github:authorize_github')


    def get(self, request, integration_id=None):
        """
        Override "get" so that integration is saved upon activation
        """
        integration = self.get_integration(request, integration_id)

        if not integration:
            """
            Here we have the integration directly when user first added integration.

            This is needed because to generate webhook url, we needed to have a saved
            integration first.
            """
            service = Service.objects.get(label=self.service_label)
            integration = Integration(service_id=self.service_label,
                                      name=service.app_config.verbose_name,
                                      user=request.user)
            integration.save()

            access_token = OAuthToken.objects.get(user=integration.user, client=ACCESS_TOKEN_CLIENT)
            resp = requests.get("https://api.github.com/user",
                                params={'access_token': access_token.access_token},
                                headers={'Accept': 'application/json'})

            if resp.status_code != 200:
                # TODO: handle unexpect error
                pass

            initial_integration_setting = {
                SETTING_KEY_GITHUB_USER_ID: resp.json()['id'],
                SETTING_KEY_WEBHOOK_SECRET: uuid.uuid4().__str__(),
                SETTING_KEY_PROJECT: request.user.get_inbox_project()
            }

            integration.update_settings(**initial_integration_setting)

            redirect_uri = request.build_absolute_uri(
                reverse('github:edit_integration', kwargs={"integration_id": integration.id}))

            return redirect(redirect_uri)

        return generic_views.EditIntegrationView.get(self, request, integration.id)


@login_required
def authorize_github(request):
    redirect_uri = request.build_absolute_uri(reverse('github:authorize_github_done'))
    oauth_state_str = str(uuid.uuid4())
    request.session[OAUTH_STATE_SESSION_KEY] = oauth_state_str

    auth_uri = extend_qs(GITHUB_AUTHORIZE_ENDPOINT,
                         client_id=settings.GITHUB_CLIENT_ID,
                         scope="user,repo",
                         redirect_uri=redirect_uri,
                         state=oauth_state_str)

    return render(request, 'github/authorize_github.html',
                  {'auth_uri': auth_uri})


@login_required
def authorize_github_done(request):
    received_state = request.GET['state']
    expected_state = request.session.pop(OAUTH_STATE_SESSION_KEY, None)

    if not received_state == expected_state:
        raise PowerAppError("Invalid state")

    authorization_code = request.GET['code']
    redirect_uri = request.build_absolute_uri(reverse('github:authorize_github_done'))

    resp = requests.post(GITHUB_ACCESS_TOKEN_ENDPOINT, data={
        'client_id': settings.GITHUB_CLIENT_ID,
        'client_secret': settings.GITHUB_CLIENT_SECRET,
        'code': authorization_code,
        'redirect_url': redirect_uri
    }, headers={'Accept': 'application/json'})

    if resp.status_code != 200:
        error = resp.headers.get('X-Error', 'Unknown Error')
        return render(request, 'github/authorize_github_done.html', {'error': error})

    access_token = resp.json()['access_token']
    OAuthToken.register(request.user, ACCESS_TOKEN_CLIENT, access_token)

    redirect_target = request.session.pop('github_auth_redirect', None)
    if not redirect_target:
        redirect_target = 'github:add_integration'

    return redirect(redirect_target)


def is_assignee(issue_event, github_user_id):
    if ('assignee' not in issue_event
            or issue_event['assignee'] is None):
        return False

    return issue_event['assignee']['id'] == github_user_id


def create_task_from_issue(integration, issue_data):
    with integration.api.autocommit():
        item_content = "%s (%s)" % (issue_data["html_url"], issue_data["title"])
        target_project = integration.settings[SETTING_KEY_PROJECT]
        item = integration.api.add_item(item_content, project_id=target_project)
        mapping_record = GithubItemIssueMap(integration=integration,
                                            issue_id=issue_data['id'],
                                            issue_url=issue_data['url'],
                                            task_id=item['id'])
        mapping_record.save()


@csrf_exempt
def webhook(request, integration_id):
    integration = get_object_or_404(Integration, id=integration_id)
    assert isinstance(integration.api, StatelessTodoistAPI)  # IDE hint
    github_user_id = integration.settings[SETTING_KEY_GITHUB_USER_ID]

    # ignore everything which is not an issue event
    if not request.META.get("HTTP_X_GITHUB_EVENT") == "issues":
        return HttpResponse()

    # payload verification
    received_hmac = request.META.get("HTTP_X_HUB_SIGNATURE")
    hmac_key = integration.settings['webhook_secret']
    actual_hmac = hmac.new(force_bytes(hmac_key), request.body, sha1).hexdigest()
    if received_hmac != ('sha1=' + actual_hmac):
        raise Http404("")

    event_payload = json.loads(force_text(request.body))
    issue_data = event_payload["issue"]


    # NOTE: Here we purposely ignore "opened" event type because when a
    # issue is open and assigned, two webhook event request (opened, assigned) are sent

    if ((event_payload["action"] == "assigned" or event_payload["action"] == "reopened")
            and is_assignee(issue_data, github_user_id)):
        try:
            item_issue_record = GithubItemIssueMap.objects.get(integration=integration,
                                                               issue_id=issue_data['id'])
            item_issue_record.save()
            # item should already existed. Do nothing now
        except GithubItemIssueMap.DoesNotExist:
            create_task_from_issue(integration, issue_data)

    if event_payload["action"] == "closed":
        with integration.api.autocommit():
            try:
                item_issue_record = GithubItemIssueMap.objects.get(integration=integration,
                                                                   issue_id=issue_data['id'])
            except GithubItemIssueMap.DoesNotExist:
                return HttpResponse("ok")

            integration.api.item_update(item_issue_record.task_id,
                                        checked=True,
                                        in_history=True)
            item_issue_record.delete()

    return HttpResponse("ok")
