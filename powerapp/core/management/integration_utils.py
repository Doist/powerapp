# -*- coding: utf-8 -*-
import time
from django.utils.six import wraps
from logging import getLogger


logger = getLogger(__name__)


class operation_limit(object):
    """
    A decorator for functions accepting just one integration to make
    sure the function is not executed more often than once in `timeout`
    seconds.

    We use `settings_key` to keep track of last execution time.
    """

    def __init__(self, last_op_settings_key, timeout=60):
        self.last_op_settings_key = last_op_settings_key
        self.timeout = timeout

    def __call__(self, function):
        @wraps(function)
        def wrapper(integration):
            now = int(time.time())
            last_op = integration.settings.get(self.last_op_settings_key, 0)
            if last_op + self.timeout > now:
                logger.info('Operation %s(%r) skipped because of operation limit', function.__name__, integration)
                return
            else:
                try:
                    return function(integration)
                finally:
                    integration.update_settings(**{self.last_op_settings_key: now})
        return wrapper
