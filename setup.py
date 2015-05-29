#!/usr/bin/env python
from setuptools import setup, find_packages


def read(filename):
    try:
        return open(filename).read()
    except IOError:
        pass


setup(name='powerapp',
      version='0.2',
      url='https://github.com/Doist/powerapp',
      license='BSD',
      zip_safe=False,
      description='The app to integrate Todoist with third-party service',
      long_description=read('README.rst'),
      packages=find_packages(),
      install_requires=[
          'todoist-python',
          'Django>=1.8',
          'django-environ',
          'django-picklefield',
          'colorlog',
          'requests',
          'feedparser'],
      entry_points={},
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
      ])
