PowerApp
--------
PowerApp is a tool to extend the functionality of your Todoist account by
integrating it with third-party applications.


Quick setup instructions with Heroku
------------------------------------

The easiest way to try out the PowerApp is to install it on Heroku plartform.
Heroku is a service hosting platform, and it allows you to run small
applications for free. PowerApp easily fits into this category, so enjoy.

Before the start you need to create some accounts here and there first.

1. Come up with a name for your installation. Requirements for the name is
   roughly same as requirements to domain names: lowercase latin letters with
   optional dashes and numbers, unique enough to avoid clashes when you create
   your app on Heroku. Something like `<myname>-powerapp`, where `myname` is your
   first name, nickname or the name of your company, could be a good start.

2. Log in with your Todoist account and create a new
   application in `Todoist Management Console <https://developer.todoist.com/appconsole.html>`_
   "App Display Name" can be anything, and since we decided to launch the app
   on Heroku, the App Service URL has to be `https://<myname>-powerapp.herokuapp.com`.

3. In application settings, set up "OAuth Redirect URL". The value has to be
   `https://<myname>-powerapp.herokuapp.com/oauth2cb/`

   .. image:: powerapp/core/static/readme_app_settings.png

   Also, set the "Webhook callback URL". The value has to be
   `https://<myname>-powerapp.herokuapp.com/webhooks/accept/`

Todoist part of the configuration is done, but don't close the window yet. It
will be needed to copy access requisites on the next step. Let's move forward
with the Heroku installation.

1. Click on a button below to launch the instant set up wizard.

    .. image:: https://www.herokucdn.com/deploy/button.png
       :alt: Deploy to Heroku
       :target: https://heroku.com/deploy?template=https://github.com/Doist/powerapp

2. Fill in required fields.

   The name

   .. image:: powerapp/core/static/readme_heroku_app_name.png

   App settings

   .. image:: powerapp/core/static/readme_heroku_config.png

   Click "Deploy for Free" button. After a while the application will be
   deployed and started on your account.

   .. image:: powerapp/core/static/readme_heroku_success.png


If everything is okay, click "View", open the application on your domain and
try to sign up for the first time.


Current status of the application
---------------------------------

The application is currently in alpha, which means that the application might
not be stable enough for regular day-to-day use, and sometimes may work not
as expected, therefore we encourage to test how the application works yourself.
If you find some bugs or rough corners, feel free to create a bug report on
GitHub, or even better, send us a pull request with a fix :)

Current list of integrations
----------------------------

There's not a lot of built-in integrations at this point. We have just two of
them, and they serve mostly the demo purpose to show developers how to create
PowerApp services:

- `Cat Comments <https://github.com/Doist/powerapp/tree/master/powerapp/contrib/catcomments>`_
  is the app to boost your morale when it's low. It adds a note with a cat
  picture to every new task you create.
- `HackerNews feed <https://github.com/Doist/powerapp/tree/master/powerapp/contrib/hackernews>`_
  pools the `hackernews feed <https://news.ycombinator.com/>`_ and adds tasks
  with links to your Todoist account in a separate project.

You don't need to install anything besides the PowerApp itself, to make them
work.

Third-party integrations
------------------------

Here is a list of custom integrations. They all have to be installed separately,
most of them require integration with third-party services, and thus extra
configuration with secret keys or something like this. Please read corresponding
installation instructions.

- `Pocket integration <https://github.com/Doist/powerapp-pocket>`_

If you have your own integration, and want it to be in this list, please create
a pull request.
