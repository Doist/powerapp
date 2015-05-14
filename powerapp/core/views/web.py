# -*- coding: utf-8 -*-
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
from powerapp.core.exceptions import PowerAppError

from powerapp.core.models import Service, Integration
from powerapp.core import oauth


@login_required
def dashboard(request):
    integrations = Integration.objects.filter(user=request.user)
    return render(request, 'dashboard.html',  {
        'active': 'dashboard',
        'integrations': integrations
    })


@login_required
def services(request):
    return render(request, 'services.html', {
        'active': 'services',
        'services': Service.objects.all()
    })


def login(request):
    if request.user.is_authenticated():
        return redirect('web_index')

    client = oauth.get_client_by_name('todoist')
    authorize_url = client.get_authorize_url(request)
    client.set_state(request)
    return render(request, 'login.html', {'authorize_url': authorize_url})


def logout(request):
    auth.logout(request)
    return redirect('web_index')


def oauth2cb(request):
    try:
        client = oauth.get_client_by_state(request)
        code = request.GET['code']
        access_token, refresh_token = client.exchange_code_for_token(request, code)
    except PowerAppError as e:
        return render(request, 'oauth2cb.html', {'error': str(e)})

    client.callback_fn(client=client,
                       access_token=access_token,
                       refresh_token=refresh_token,
                       request=request)

    return redirect(client.oauth2cb_redirect_uri)


@require_POST
@login_required
def delete_integration(request, service_id, integration_id):
    user = request.user
    integration = get_object_or_404(Integration, id=integration_id, user=user)
    integration.delete()
    messages.info(request, "Integration '%s' deleted" % integration.name)
    return redirect(reverse('web_index'))


@login_required
def edit_integration(request, service_id, integration_id):
    return redirect('%s:edit_integration' % service_id, integration_id)
