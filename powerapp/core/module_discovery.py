import os
from importlib import import_module
import inspect

from django.utils import six


def scan_package_for_instances(module_name_or_instance, base_class):
    object_matcher = lambda obj: isinstance(obj, base_class)
    return scan_package_for_objects(module_name_or_instance, object_matcher)


def scan_package_for_objects(module_name_or_instance, object_matcher):
    """
    Scan package and all first-level subpackages for objects of a certain
    kind.

    `object_matcher` is a function accepting an object and returning True or False

    For example, there is a structure::


        app/module/__init__.py
                  foo.py
                  bar.py

    We may ask for something like::

        scan_package_for_objects("app.module", lambda obj: isinstance(obj, basestring))

    and it finds all globally defined strings
    """
    if isinstance(module_name_or_instance, six.string_types):
        module_name = module_name_or_instance
        pkg = import_module(module_name_or_instance)
    else:
        module_name = module_name_or_instance.__name__
        pkg = module_name_or_instance

    ret = []
    ret += [m for _, m in inspect.getmembers(pkg, object_matcher)]

    pkg_filename = pkg.__file__
    pkg_basename, _ = os.path.splitext(os.path.basename(pkg_filename))
    if pkg_basename != '__init__':
        return ret

    pkg_dir = os.path.dirname(pkg_filename)
    for filename in sorted(os.listdir(pkg_dir)):
        basename, ext = os.path.splitext(filename)
        if basename == '__init__' or ext != '.py':
            continue

        mod = import_module('%s.%s' % (module_name, basename))
        ret += [m for _, m in inspect.getmembers(mod, object_matcher)]

    return ret


def collect_settings():
    pass
    """
    for service in Service.objects.all():
        try:
            loader = SourceFileLoader("", service.root + '/settings.py')
            app_settings = loader.load_module()
            setattr(settings, service.id, app_settings)
        except FileNotFoundError:
            continue
    """
