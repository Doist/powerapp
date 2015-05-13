from django.apps import apps
from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


def app_urls():
    """
    Automatically add URLs from applications which want to register their URLs

    In order to do so, the application has to have a urlpatterns() method,
    returning the list of url objects for inclusion.

    By default though (see `powerapp.core.apps:ServiceAppConfig.urlpatterns`)
    every service app just returns its own urls.py for inclusion
    """
    ret = []
    for app in apps.get_app_configs():
        if hasattr(app, 'urlpatterns'):
            ret += app.urlpatterns()
    return ret


urlpatterns = [
    url(r'', include('powerapp.core.urls'))
]
urlpatterns += list(staticfiles_urlpatterns())
urlpatterns += app_urls()
