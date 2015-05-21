Integration tests require a bit of preliminary actions to work.

Set up webhooks
---------------

First, we have to make tests accept webhooks from the "real world Todoist".
For that purpose the test suite runs a django live server listening for
a local host and port, and additionally, we start a ngrok server to create a
tunnel so that your local address could be available from the Internet.

Visit the `Todoist app_console <https://todoist.com/app_console>`_ and create
a new application. The application has to emit all webhooks and the webhook
URL has to look like `https://yourname.ngrok.com/webhooks/accept/`, where
"yourname" is something "yours".

The visit `the ngrok project website <https://ngrok.com/>`_, download ngrok for
your platform. In order to be able to use it with custom subdomains, you have
to sign up there (for free) and obtain your personal auth token.

Set up environment variables::

    TEST_NGROK_SUBDOMAIN=yourname
    TEST_NGROK_AUTH_TOKEN=xxx-xxxxxxxxxx

Start tests. If everything goes well, webhooks will be sent to
yourname.ngrok.com and forwarded to your local test server.


Set up premium account
----------------------

Create a premium account for testing purposes. If you are a developer, you
may ask for the Support section to create a free premium testing account
for you.

::

    TEST_PREMIUM_EMAIL=premium.foo@example.com
    TEST_PREMIUM_PASSWORD=password
