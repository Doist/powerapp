# -*- coding: utf-8 -*-

import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.forms import fields
from django.http import Http404, HttpResponse

from powerapp.core import django_fields
from powerapp.core.models.integration import Integration
from powerapp.core import django_forms, generic_views
from powerapp.core.models.oauth import OAuthToken
from powerapp.core.web_utils import extend_qs
from powerapp.core.sync import StatelessTodoistAPI
from .models import GithubItemIssueMap


GITHUB_AUTHORIZE_ENDPOINT = 'https://github.com/login/oauth/authorize'
GITHUB_ACCESS_TOKEN_ENDPOINT = 'https://github.com/login/oauth/access_token'


class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'github'
    project = django_fields.ProjectChoiceField(label=u'Project to github tasks to')


class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'github'
    access_token_client = 'github'
    form = IntegrationForm

    def extra_template_context(self, request, integration):
        webhook_url = self.request.build_absolute_uri(
            reverse('github:webhook', kwargs={"integration_id": integration.id}))

        return {
            "webhook_url": webhook_url
        }

    def access_token_redirect(self, request):
        request.session['github_auth_redirect'] = request.path
        return redirect('github:authorize_github')


@login_required
def authorize_github(request):
    redirect_uri = request.build_absolute_uri(reverse('github:authorize_github_done'))

    print('client id', settings.GITHUB_CLIENT_ID)

    # TODO: better state generation, change scope
    auth_uri = extend_qs(GITHUB_AUTHORIZE_ENDPOINT,
                         client_id=settings.GITHUB_CLIENT_ID,
                         scope="user",
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
    OAuthToken.register(request.user, 'github', access_token)

    redirect_target = request.session.pop('github_auth_redirect', None)
    if not redirect_target:
        redirect_target = 'github:add_integration'

    return redirect(redirect_target)


@csrf_exempt
def webhook(request, *args, **kwargs):
    integration_id = kwargs.get("integration_id")

    if not integration_id:
        raise Http404("")

    integration = get_object_or_404(Integration, id=integration_id)
    assert isinstance(integration.api, StatelessTodoistAPI)  # IDE hint

    print('header', request.META)

    if not request.META.get("HTTP_X_GITHUB_EVENT") == "issues":
        raise Http404("")

    # TODO: add payload verification
    payload_digest = request.META.get("HTTP_X_HUB_SIGNATURE")

    event_payload = json.loads(
        request.body.decode(encoding='UTF-8'))

    if not event_payload["action"] == "opened":
        return HttpResponse("ok")

    issue_data = event_payload["issue"]

    if event_payload["action"] == "opened":
        with integration.api.autocommit():
            item_content = "%s (%s)" % (issue_data["html_url"], issue_data["title"])
            item = integration.api.add_item(item_content)
            mapping_record = GithubItemIssueMap(integration=integration,
                                                issue_id=issue_data['id'],
                                                task_id=item['id'])
            mapping_record.save()

        return HttpResponse("ok")

