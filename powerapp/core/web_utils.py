# -*- coding: utf-8 -*-
from django.utils.six.moves.urllib import parse
from django.utils.encoding import force_bytes
from django.conf import settings


def extend_qs(base_url, **kwargs):
    """
    Extend querystring of the URL with kwargs, taking care of python types.

    - True is converted to "1"
    - When a value is equal to False or None, then corresponding key is removed
      from the querystring at all. Please note that empty strings and numeric
      zeroes are not equal to False here.
    - Unicode is converted to utf-8 string
    - Everything else is converted to string using str(obj)

    For instance:

    >>> extend_querystring('/foo/?a=b', c='d', e=True, f=False)
    '/foo/?a=b&c=d&e=1'
    """
    parsed = parse.urlparse(base_url)
    query = dict(parse.parse_qsl(parsed.query))
    for key, value in kwargs.items():
        value = convert_to_string(value)
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    query_str = parse.urlencode(query)
    parsed_as_list = list(parsed)
    parsed_as_list[4] = query_str
    return parse.urlunparse(parsed_as_list)


def convert_to_string(value):
    """
    Helper function converting python objects to strings

    None is special value menaning "remove me from the queryset"
    """
    if value is None or value is False:
        return None
    if value is True:
        return b'1'
    return force_bytes(value)


def build_absolute_uri(relative_url):
    """
    Build absolute URL from a relative one. If the URL is already absolute,
    keep it as is
    """
    return parse.urljoin(settings.SITE_URL, relative_url)
