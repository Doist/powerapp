# -*- coding: utf-8 -*-
import os
import importlib
import pkg_resources


def app_discovery():
    """
    Find integrations (as strings) to populate INSTALLED_APPS
    """
    ret = []

    # search in contrib
    contrib_root = 'powerapp.contrib'
    contrib = importlib.import_module(contrib_root)
    dirname = os.path.dirname(os.path.abspath(contrib.__file__))
    for subdir in os.listdir(dirname):
        if subdir == '__pycache__':
            continue
        if os.path.isdir(os.path.join(dirname, subdir)):
            ret.append('%s.%s' % (contrib_root, subdir))

    # search in external services
    for ep in pkg_resources.iter_entry_points('powerapp_services'):
        ret.append(ep.module_name)

    return ret
