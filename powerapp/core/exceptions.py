# -*- coding: utf-8 -*-
import logging


logger = logging.getLogger(__name__)


def return_or_raise(result):
    """
    Take the result of sync operation and pass it through if everything is
    okay, or raise PowerAppError, if there is an error
    """
    if result is None:
        return result

    if not isinstance(result, dict):
        raise PowerAppError(result)

    if 'error' in result:
        err = result['error']
        logger.error(err)
        raise PowerAppError(err)
    return result


class PowerAppError(Exception):
    """
    Base class for all "managed exceptions" we raise
    """
    pass
