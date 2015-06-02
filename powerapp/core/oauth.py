"""
Generic functions to register OAuth 2.0 clients can be implemented like this:

.. code-block:: python

    @register_oauth_client('github')
    def github_client():
        ...

By convention, for the callback client "foo" settings
"FOO_CLIENT_ID" and "FOO_CLIENT_SECRET", required for the OAuth flow have to
be defined.

The callback function will be called from the `oauth2cb`

"""
import datetime
import uuid
from logging import getLogger

import requests
from django.core.urlresolvers import reverse
from django.conf import settings
from requests_oauthlib import OAuth2Session

from django.utils.six.moves.urllib import parse
from powerapp.core.exceptions import PowerAppError
from powerapp.core.models.oauth import OAuthToken
from powerapp.core.web_utils import extend_qs, ensure_https

oauth_clients = {}

LIVE_TIME_ACCESS_TOKEN = 2000  # seconds

logger = getLogger(__name__)


def base_response_parser(resp):
    return resp.json()


class register_oauth_client(object):
    """
    Decorator to register new OAuth client.
    """

    def __init__(self, name, authorize_endpoint, access_token_endpoint,
                 scope=None,
                 client_id=None, client_secret=None,
                 callback_class=None,
                 oauth2cb_redirect_uri='/',
                 redirect_uri_required=True,
                 response_parser=base_response_parser):
        self.name = name
        self.response_parser = response_parser
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_class = callback_class or OAuthClient
        self.oauth2cb_redirect_uri = oauth2cb_redirect_uri
        self.redirect_uri_required = redirect_uri_required

    def __call__(self, fn):
        instance = self.callback_class(self.name, fn,
                                       self.authorize_endpoint,
                                       self.access_token_endpoint,
                                       scope=self.scope,
                                       client_id=self.client_id,
                                       client_secret=self.client_secret,
                                       oauth2cb_redirect_uri=self.oauth2cb_redirect_uri,
                                       response_parser=self.response_parser)
        oauth_clients[self.name] = instance
        return fn


def get_client_by_name(name):
    """
    Return OAuth client by name

    :rtype: OAuthClient
    """
    try:
        return oauth_clients[name]
    except KeyError:
        raise RuntimeError('OAuth client %r not registered' % name)


def get_client_by_state(request):
    """
    Return OAuth client by state stored in session
    """
    server_error_codes = {
        'redirect_uri_mismatch': u'Redirect URI mismatch',
        'access_denied': u'Access denied',
    }

    if 'error' in request.GET:
        error_code = request.GET.get('error')
        error_message = server_error_codes.get(error_code, u'Unknown error')
        raise PowerAppError(error_message)

    if 'state' not in request.GET:
        raise PowerAppError('Request does not have a "state" parameter')

    state = request.GET['state']
    state_dict = dict(parse.parse_qsl(state or ''))
    if 'name' not in state_dict or 'secret' not in state_dict:
        raise PowerAppError("Invalid state")

    session_key = get_oauth_state_session_name(state_dict['name'])
    session_value = request.session.pop(session_key, None)
    if not session_value:
        raise PowerAppError("Session value not found")
    if state != session_value:
        raise PowerAppError("Invalid state")
    return get_client_by_name(state_dict['name'])


def get_oauth_state_session_name(name):
    return '%s_oauth_state' % name


class OAuthClient(object):
    """
    Base class for OAuth client. Instances are generated automatically from
    `register_oauth_client` decorator and can be accessed by
    `get_client_by_name` functions
    `oauth2cb_redirect_uri' - redirect url for oauth2cb function
    """

    def __init__(self, name, callback_fn, authorize_endpoint,
                 access_token_endpoint, scope=None, client_id=None,
                 client_secret=None, oauth2cb_redirect_uri='/',
                 redirect_uri_required=True, response_parser=base_response_parser):
        self.authorize_endpoint = authorize_endpoint
        self.access_token_endpoint = access_token_endpoint
        self.name = name
        self.response_parser = response_parser
        self.callback_fn = callback_fn
        self.scope = scope
        self.client_id = client_id or '%s_CLIENT_ID' % name.upper()
        self.client_secret = client_secret or '%s_CLIENT_SECRET' % name.upper()
        self.oauth2cb_redirect_uri = oauth2cb_redirect_uri
        self.state = None
        self.redirect_uri_required = redirect_uri_required

    def get_client_id(self):
        return getattr(settings, self.client_id)

    def get_client_secret(self):
        return getattr(settings, self.client_secret)

    def get_oauth2cb_uri(self, request):
        return ensure_https(request.build_absolute_uri(reverse('web_oauth2cb')))

    def get_authorize_url(self, request, **kwargs):
        """
        :param kwargs: extra params for authorize url which will overwrite
                       default params
        """
        qs = {
            'client_id': self.get_client_id(),
            'scope': self.scope or '',
            'state': self.create_state(),
            'response_type': 'code',
        }
        if self.redirect_uri_required:
            qs['redirect_uri'] = self.get_oauth2cb_uri(request)
        qs.update(kwargs)
        return extend_qs(self.authorize_endpoint, **qs)

    def exchange_code_for_token(self, request, code):
        post_data = {
            'client_id': self.get_client_id(),
            'client_secret': self.get_client_secret(),
            'code': code,
            'grant_type': 'authorization_code',
        }
        if self.redirect_uri_required:
            post_data['redirect_uri'] = self.get_oauth2cb_uri(request)
        resp = requests.post(self.access_token_endpoint, data=post_data)
        if resp.status_code != 200:
            logger.error('Unable to exchange OAuth code for token. '
                         'Server said %r', resp.content)
            raise PowerAppError(resp.content)

        return self.response_parser(resp)

    def save_token(self, user, token):
        kwargs = {
            'user': user,
            'client': self.name,
            'access_token': token['access_token'],
        }
        for extra_field in ['expires_in', 'refresh_token', 'token_type']:
            if extra_field in token:
                kwargs[extra_field] = token[extra_field]
        return OAuthToken.register(**kwargs)

    """
    def check_refresh_token(self, user):
        access_token = OAuthToken.get_by_client(user, self.name)
        if (access_token.time - datetime.datetime.now()).total_seconds > LIVE_TIME_ACCESS_TOKEN:
            self.refresh_token(user)

    def refresh_token(self, user):
        refresh_token = RefreshToken.objects.get(user=user, client=self.name)
        post_data = {
            'client_id': self.get_client_id(),
            'client_secret': self.get_client_secret(),
            'refresh_token': refresh_token.token,
            'grant_type': 'refresh_token',
        }
        resp = requests.post(self.access_token_endpoint, data=post_data)
        resp.raise_for_status()

        self.save_access_token(user, resp.json()['access_token'])
    """

    def create_state(self):
        """
        Create the state value (as a string)

        We use this state to validate the response
        from the third party and to get to know the callback URL.

        1. Cookie name is "xxxx_oauth_state" (for example, "todoist_oauth_state")
        2. It's value (the same value we pass through the OAuth loop):
           `name=<oauth_client_name>&secret=<random_secret>&redirect=<callback_url>`
           (here redirect is the page where the account has to be redirected on success)
        """
        redirect_url = reverse('web_index')
        state = parse.urlencode({'name': self.name,
                                 'secret': uuid.uuid4(),
                                 'redirect': redirect_url})
        self.state = state
        return state

    def set_state(self, request):
        session_key = get_oauth_state_session_name(self.name)
        request.session[session_key] = self.state

    def get_state(self, request):
        session_key = get_oauth_state_session_name(self.name)
        return request.session.get(session_key)

    def parse_state(self, state):
        return dict(parse.parse_qsl(state or ''))

    def get_oauth2_session(self, user):
        """
        Return the OAuth2 session client, which among others, knows how to
        upgrade the access token with a refresh token value
        """
        # warning: oauth token may not exist, we should probably wrap this with
        # a less generic exception
        oauth_token = OAuthToken.objects.get(user=user, client=self.name)
        token_dict = {
            'access_token': oauth_token.access_token,
            'expires_in': oauth_token.get_expires_in(),
            'refresh_token': oauth_token.refresh_token,
            'token_type': oauth_token.token_type,
        }

        def token_updater(token):
            oauth_token.refresh(token)

        session = OAuth2Session(client_id=self.get_client_id(),
                                auto_refresh_url=self.access_token_endpoint,
                                auto_refresh_kwargs={
                                    'client_id': self.get_client_id(),
                                    'client_secret': self.get_client_secret(),
                                },
                                token=token_dict,
                                token_updater=token_updater)
        return session
