# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
import requests
from django.shortcuts import render, redirect

from powerapp.core import django_fields
from powerapp.core import django_forms, generic_views
from powerapp.core.models.oauth import OAuthToken
from powerapp.core.web_utils import extend_qs


GITHUB_AUTHORIZE_ENDPOINT = 'https://github.com/login/oauth/authorize'
GITHUB_ACCESS_TOKEN_ENDPOINT = 'https://github.com/login/oauth/access_token'

CLIENT_ID = "e9914ad98b5b53882a50"
CLIENT_SECRET = "00a46c84b532fe23abbfe8b325b94bf656d9d529"


class IntegrationForm(django_forms.IntegrationForm):
    service_label = 'github'
    project = django_fields.ProjectChoiceField(label=u'Project to github tasks to')


class EditIntegrationView(generic_views.EditIntegrationView):
    service_label = 'github'
    access_token_client = 'github'
    form = IntegrationForm

    def access_token_redirect(self, request):
        request.session['github_auth_redirect'] = request.path
        return redirect('github:authorize_github')


@login_required
def authorize_github(request):
    redirect_uri = request.build_absolute_uri(reverse('github:authorize_github_done'))

    # TODO: better state generation
    auth_uri = extend_qs(GITHUB_AUTHORIZE_ENDPOINT,
                         client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
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
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
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


