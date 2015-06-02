# -*- coding: utf-8 -*-
from powerapp.core.models.oauth import AccessToken, RefreshToken
from powerapp.core.oauth import register_oauth_client


OAUTH_CLIENT_NAME = 'gcal'
GCAL_SCOPE = 'https://www.googleapis.com/auth/calendar'


@register_oauth_client(OAUTH_CLIENT_NAME,
                       authorize_endpoint='https://accounts.google.com/o/oauth2/auth',
                       access_token_endpoint='https://www.googleapis.com/oauth2/v3/token',
                       scope='https://www.googleapis.com/auth/calendar',
                       client_id='GOOGLE_CLIENT_ID',
                       client_secret='GOOGLE_CLIENT_SECRET',
                       oauth2cb_redirect_uri='gcal_sync:add_integration')
def gcal_oauth(client, access_token, request, **kwargs):
    AccessToken.register(request.user, OAUTH_CLIENT_NAME, GCAL_SCOPE, access_token)
    refresh_token = kwargs.get('refresh_token')
    if refresh_token:
        RefreshToken.register(request.user, OAUTH_CLIENT_NAME, GCAL_SCOPE, refresh_token)
