# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login
from django.http import Http404
from django.conf import settings

from powerapp.core.oauth import register_oauth_client
from powerapp.core.models.user import User
from powerapp.core.exceptions import PowerAppError


@register_oauth_client('todoist',
                       authorize_endpoint='%s/oauth/authorize' % settings.API_ENDPOINT,
                       access_token_endpoint='%s/oauth/access_token' % settings.API_ENDPOINT,
                       scope='data:read_write,data:delete,project:delete',
                       redirect_uri_required=False)
def todoist_oauth(client, access_token, request, **kwargs):
    try:
        user = User.objects.register(access_token)
    except PowerAppError:
        raise Http404()
    client.save_access_token(user, access_token)
    check_user = authenticate(user=user)
    login(request, check_user)
