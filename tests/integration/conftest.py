# -*- coding: utf-8 -*-
import pytest
import todoist
import time
import requests
import environ
from django.conf import settings
from powerapp.core.models import Integration, User


env = environ.Env()
TEST_NGROK_SUBDOMAIN = env('TEST_NGROK_SUBDOMAIN')
TEST_NGROK_AUTH_TOKEN = env('TEST_NGROK_AUTH_TOKEN')
TEST_PREMIUM_EMAIL = env('TEST_PREMIUM_EMAIL')
TEST_PREMIUM_PASSWORD = env('TEST_PREMIUM_PASSWORD')


@pytest.fixture(scope='session')
def ngrok(live_server, xprocess):
    port = live_server.url.rsplit(':', 1)[-1]

    def preparefunc(cwd):
        pattern = 'Tunnel established'
        args = ['ngrok',
                '-authtoken', TEST_NGROK_AUTH_TOKEN,
                '-log', 'stdout',
                '-subdomain', TEST_NGROK_SUBDOMAIN,
                port]
        return pattern, args

    logfile = xprocess.ensure("ngrok", preparefunc)
    return logfile


@pytest.yield_fixture(scope='session')
def api():
    """
    Get a premium Todoist user and returns the API object to work with it
    """
    # and now, follow the password grant OAuth flow to make sure webhooks work
    access_token = get_access_token(TEST_PREMIUM_EMAIL, TEST_PREMIUM_PASSWORD)
    api = TodoistAPI(access_token, api_endpoint=settings.API_ENDPOINT)
    api.sync(resource_types=['user', 'projects', 'items', 'notes'])

    yield api

    # delete tasks
    api.sync(resource_types=['user', 'projects', 'items', 'notes'])
    for item in api.items.all():
        item.delete()

    # delete projects (everything except inbox)
    for project in api.projects.all():
        if project['id'] != api.user.get('inbox_project'):
            project.delete()

    api.commit()


@pytest.fixture
def user(api, db):
    return User.objects.create(id=api.user.get('id'),
                               email=api.user.get('email'),
                               api_token=api.token)


@pytest.fixture
def catcomments_integration(api, user, catcomments_service):
    """
    Create a "catcomments" integration
    """
    s = {'project': api.user.get('inbox_project')}
    return Integration.objects.create(service=catcomments_service,
                                      name='Cat Comments',
                                      user=user,
                                      settings=s)


class TodoistAPI(todoist.TodoistAPI):
    """
    A slightly extended version of the standard API client
    """
    DEFAULT_RESOURCE_TYPES = ['projects', 'items', 'notes']


    def wait_for_update(self, timeout=15,
                        resource_types=DEFAULT_RESOURCE_TYPES):
        """
        Wait for the update for at least timeout minutes.

        The functions wait for any updates in projects, items or notes in
        user's Todoist account by polling it. If nothing has changed withing
        `timeout` minutes, it raises the RuntimeError.

        Upon successful exit the local state of the object is synchronized
        with Todoist.
        """
        start = time.time()
        delay = 0.5
        while True:
            # if something has changed on the server side, the server returns
            # non-empty list with results, like
            # {..., "Projects": [..], "Items": [...]}
            result = self.sync(resource_types=resource_types)
            for value in result.values():
                if isinstance(value, list) and len(value) > 0:
                    return

            # timeout
            if time.time() - start > timeout:
                raise RuntimeError('No updates in %r within %s sec' % (resource_types, timeout))

            # wait a bit more
            print('Wait %s sec...' % delay)
            time.sleep(delay)
            delay *= 2


def get_access_token(email, password, scope='data:read_write,data:delete,project:delete'):
    """
    Helper function to exchange email and password to access token
    """
    data = {
        'client_id': settings.TODOIST_CLIENT_ID,
        'client_secret': settings.TODOIST_CLIENT_SECRET,
        'grant_type': 'password',
        'username': email,
        'password': password,
        'scope': scope,
    }
    url = settings.API_ENDPOINT + '/oauth/access_token'
    resp = requests.post(url, data=data)
    return resp.json()['access_token']
