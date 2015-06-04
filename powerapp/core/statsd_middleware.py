# -*- coding: utf-8 -*-
import inspect
import time
from django_statsd.clients import statsd


class GrafanaRequestTimingMiddleware(object):
    """statsd's timing data per view stored as gauges"""

    def process_view(self, request, view_func, view_args, view_kwargs):
        view = view_func
        if not inspect.isfunction(view_func):
            view = view.__class__
        try:
            request._view_module = view.__module__
            request._view_name = view.__name__
            request._start_time = time.time()
        except AttributeError:
            pass

    def process_response(self, request, response):
        self._record_time(request)
        return response

    def process_exception(self, request, exception):
        self._record_time(request)

    def _record_time(self, request):
        if hasattr(request, '_start_time'):
            ms = int((time.time() - request._start_time) * 1000)
            data = dict(module=request._view_module, name=request._view_name,
                        method=request.method)
            statsd.gauge('view.response_ms.{module}.{name}.{method}'.format(**data), ms)
            statsd.gauge('view.response_ms.{module}.{method}'.format(**data), ms)
            statsd.gauge('view.response_ms.{method}'.format(**data), ms)
