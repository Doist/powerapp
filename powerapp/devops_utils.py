# -*- coding: utf-8 -*-
"""
Utility functions to simplify the deployment process
"""
import os
import re
from logging import getLogger
import subprocess


def extend_requirements_txt():
    """
    Extend requirements.txt with extra requirements from POWERAPP_SERVICES
    """
    requirements = [r.strip() for r in open('requirements.txt').readlines()]
    for req in get_extra_requirements():
        req_str = ' '.join(req)
        if req_str not in requirements:
            requirements.append(req_str)
    with open('requirements.txt', 'w') as fd:
        fd.write('\n'.join(requirements) + '\n')


def install_requirements():
    """
    Install extra requirements from POWERAPP_SERVICES
    """
    for req in get_extra_requirements():
        subprocess.call(['pip', 'install'] + req)


def get_extra_requirements():
    """
    Read POWERAPP_SERVICES environment variable, and return the list
    of extra packages to install.

    Every package in the list is a list of one (["powerapp-foo"]) or two
    (["-e", "git+git@github.com:Doist/powerapp-foo.git"]) elements
    """
    services = os.environ.get('POWERAPP_SERVICES')
    for service in re.split(r'[\s,;]+', services or ''):
        if not service:
            continue
        if service.startswith('http') and '/' in service:
            # it's a git URL, extend it with extra fields
            app_name = re.search(r'([^/]+)(.git)?$', service).group(1)
            url = 'git+%s#egg=%s' % (service, app_name)
            yield ['-e', url]
        else:
            # return as is
            yield [service]


def run_bootstrap_management_commands():
    """
    Run "bootstap management commands"
    """
    # it's inside function to make sure we can use the rest of devops_utils
    # without setting up all the Django machinery
    from django.core.management import call_command
    call_command('migrate')
    call_command('collectstatic', interactive=False)
    call_command('collect_services')
