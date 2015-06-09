# -*- coding: utf-8 -*-
from threading import local
import datetime
from contextlib import contextmanager
from django.utils.encoding import force_text


# local context to be used in logging
_local_ctx = local()


@contextmanager
def ctx(**kwargs):
    """
    context manager used to set up extra logging variables
    """
    _ensure_local_has_ctx()
    old_ctx = _local_ctx.ctx.copy()
    try:
        update_ctx(**kwargs)
        yield
    finally:
        _local_ctx.ctx = old_ctx


def update_ctx(**kwargs):
    """
    A helper function to update the context. Data will be available until
    the end of the thread, unless overwritten
    """
    _ensure_local_has_ctx()
    _local_ctx.ctx.update(**kwargs)


def get_ctx():
    """ get the dict with thread local context """
    _ensure_local_has_ctx()
    return _local_ctx.ctx


def _ensure_local_has_ctx():
    if not hasattr(_local_ctx, 'ctx'):
        _local_ctx.ctx = {}


class ContextFilter(object):
    """
    A filter which simply adds log data to the context
    """
    def __init__(self, fields=None):
        self.fields = fields or {}

    def filter(self, record):
        effective_ctx = dict(self.fields, **get_ctx())
        for k, v in effective_ctx.items():
            for processed_key, processed_value in self.process(k, v).items():
                setattr(record, processed_key, processed_value)
        return True

    def process(self, key, value):
        """ helper function to convert whatever value to dict """
        if isinstance(value, datetime.datetime):
            return {key: value.isoformat()}

        if hasattr(value, '__log__') and callable(value.__log__):
            return {'%s_%s' % (key, k): v for k, v in value.__log__()}

        return {key: force_text(value)}


class RequestContextMiddleware(object):

    def process_request(self, request):
        """
        Populate context with useful information.
        """
        # we're safe here, as long as this function is called on every request,
        # and all fields are populated
        fields = {
            # user field
            'user': request.user,
            # request-related fields
            'request_url': request.get_full_path(),
            'request_method': request.method,
            'user_agent': request.META['HTTP_USER_AGENT'],
            'remote_addr': request.META['REMOTE_ADDR'],
        }
        update_ctx(**fields)
