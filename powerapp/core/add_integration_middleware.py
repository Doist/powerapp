# -*- coding: utf-8 -*-
from django.core.urlresolvers import resolve
from django.shortcuts import redirect

from powerapp.core.models.service import Service


class AddIntegrationMiddleware(object):
    """Check Unique integration per service.
       If integration was added and flag `unique_per_user` if True
       redirect to edit page, else return response
    """

    def process_response(self, request, response):
        url_name = resolve(request.path_info).url_name
        app_name = resolve(request.path_info).app_name

        if url_name == 'add_integration':
            service = Service.objects.get(label=app_name)
            if service.has_installation() and service.unique_per_user:
                redirect_url_name = '%s:%s' % (app_name, 'edit_integration')
                return redirect(redirect_url_name, service.integration_set.get().pk)

        return response
