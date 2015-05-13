# -*- coding: utf-8 -*-
from pprint import pformat


class AttrDict(dict):
    """
    Dict allowing to get access to its keys as attributes
    """

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError('%s not found' % name)

    def __setattr__(self, name, value):
        self[name] = value

    def __repr__(self):
        formatted_dict = pformat(dict(self))
        classname = self.__class__.__name__
        return '%s(%s)' % (classname, formatted_dict)

    @property
    def __members__(self):
        return self.keys()


def recursive_attrdict(obj):
    """
    Recursively find all dicts in a stricture, and convert them to attr dict
    """
    if isinstance(obj, (dict, AttrDict)):
        return AttrDict({k: recursive_attrdict(v) for k, v in obj.items()})

    if isinstance(obj, (list, tuple, set)):
        return obj.__class__([recursive_attrdict(item) for item in obj])

    return obj
