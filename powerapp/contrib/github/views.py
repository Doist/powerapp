# -*- coding: utf-8 -*-

import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import Http404, HttpResponse

from powerapp.core import django_fields
from powerapp.core.models.integration import Integration
from powerapp.core.models import Service
from powerapp.core import django_forms, generic_views
from powerapp.core.models.oauth import OAuthToken
from powerapp.core.web_utils import extend_qs
from powerapp.core.sync import StatelessTodoistAPI
from .models import GithubItemIssueMap


GITHUB_AUTHORIZE_ENDPOINT = 'https://github.com/login/oauth/authorize'
GITHUB_ACCESS_TOKEN_ENDPOINT = 'https://github.com/login/oauth/access_token'


ACCESS_TOKEN_CLIENT = "github"
SETTING_KEY_GITHUB_USER_ID = "github_user_id"


class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'github'
    project = django_fields.ProjectChoiceField(label=u'Project to github tasks to')


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
            service = Service.objects.get(label=self.service_label)
            integration = Integration(service_id=self.service_label,
                                      name=service.app_config.verbose_name,
                                      user=request.user)
            integration.save()

            redirect_uri = request.build_absolute_uri(
                reverse('github:edit_integration', kwargs={"integration_id": integration.id}))

            return redirect(redirect_uri)

        return generic_views.EditIntegrationView.get(self, request, integration.id)


    def on_save(self, integration):
        if SETTING_KEY_GITHUB_USER_ID not in integration.settings:
            access_token = OAuthToken.objects.get(user=integration.user, client=ACCESS_TOKEN_CLIENT)
            resp = requests.get("https://api.github.com/user",
                                params={'access_token': access_token.access_token},
                                headers={'Accept': 'application/json'})

            if resp.status_code != 200:
                # TODO: handle unexpect error
                pass

            github_user_id = resp.json()['id']
            integration.update_settings(**{SETTING_KEY_GITHUB_USER_ID: github_user_id})

        return generic_views.EditIntegrationView.on_save(self, integration)


@login_required
def authorize_github(request):
    redirect_uri = request.build_absolute_uri(reverse('github:authorize_github_done'))

    # TODO: better state generation, change scope
    auth_uri = extend_qs(GITHUB_AUTHORIZE_ENDPOINT,
                         client_id=settings.GITHUB_CLIENT_ID,
                         scope="user,repo",
                         redirect_uri=redirect_uri,
                         state="abdfasfafasd")

    return render(request, 'github/authorize_github.html',
                  {'auth_uri': auth_uri})


@login_required
def authorize_github_done(request):
    # TODO: Verify state
    state = request.GET['state']

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


@csrf_exempt
def webhook(request, *args, **kwargs):
    integration_id = kwargs.get("integration_id")

    if not integration_id:
        raise Http404("")

    integration = get_object_or_404(Integration, id=integration_id)
    assert isinstance(integration.api, StatelessTodoistAPI)  # IDE hint

    if SETTING_KEY_GITHUB_USER_ID not in integration.settings:
        # TODO: unexpected error. Log it
        raise Http404("")

    github_user_id = integration.settings[SETTING_KEY_GITHUB_USER_ID]

    if not request.META.get("HTTP_X_GITHUB_EVENT") == "issues":
        raise Http404("")

    # TODO: add payload verification
    payload_digest = request.META.get("HTTP_X_HUB_SIGNATURE")

    event_payload = json.loads(
        request.body.decode(encoding='UTF-8'))

    if not event_payload["action"] == "opened":
        return HttpResponse("ok")

    issue_data = event_payload["issue"]

    if (event_payload["action"] == "opened"
            and is_assignee(issue_data, github_user_id)):
        with integration.api.autocommit():
            item_content = "%s (%s)" % (issue_data["html_url"], issue_data["title"])
            item = integration.api.add_item(item_content)
            mapping_record = GithubItemIssueMap(integration=integration,
                                                issue_id=issue_data['id'],
                                                issue_url=issue_data['url'],
                                                task_id=item['id'])
            mapping_record.save()

    # if event_payload["action"] == "closed":
    #     with integration.api.autocommit():
    #         item_issue_record = GithubItemIssueMap.objects.get(integration=integration,
    #                                                            issue_id=issue_data['id'])
    #         if not item_issue_record:
    #             return HttpResponse("ok")
    #
    #         # integration.api.item_update(item_issue_record.task_id)
    #         # mapping_record.save()

    return HttpResponse("ok")

