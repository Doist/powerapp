#!/usr/bin/env python
import sys
from setuptools import setup, find_packages

PY3 = sys.version_info.major == 3


def read(filename):
    try:
        return open(filename).read()
    except IOError:
        pass


install_requires = [
    'todoist-python',
    'Django>=1.8.2',
    'django-environ',
    'django-picklefield',
    'colorlog',
    'requests',
    'feedparser',
    'pytz',
    'raven',
    'requests-oauthlib',
    'pyRFC3339',
]


# We cannot install evernote on Python3, because the version supporting it
# is not on PyPI yet. Use the requirement from requirements.txt to set it up
if not PY3:
    install_requires.append('evernote')


setup(name='powerapp',
      version='0.2',
      url='https://github.com/Doist/powerapp',
      license='BSD',
      zip_safe=False,
      description='The app to integrate Todoist with third-party service',
      long_description=read('README.rst'),
      packages=find_packages(),
      install_requires=install_requires,
      entry_points={},
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
      ])
