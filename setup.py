#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import os
import re

try:
    import py2exe
    has_py2exe = True
except:
    has_py2exe = False

if has_py2exe:
    import pyportify
    import pyportify.views

basepath = os.path.dirname(__file__)
readme_rst = os.path.join(basepath, "README.rst")
requirements_txt = os.path.join(basepath, "requirements.txt")

with open(readme_rst) as readme:
    long_description = readme.read()

with open(requirements_txt) as reqs:
    install_requires = [
        line for line in reqs.read().split('\n') if (line and not
                                                     line.startswith('--'))
    ]


def get_version(filename):
    with open(filename) as r:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", r.read()))
        print metadata
        return metadata['version']


args = dict(
    name='pyportify',
    version=get_version("pyportify/__init__.py"),
    author='Josh Braegger',
    author_email='rckclmbr@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/rckclmbr/pyportify',
    license='Apache 2.0',
    description='App to transfer your spotify playlists to Google Play '
                'Music',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Flask',
    ],
    entry_points={
        'console_scripts': [
            'pyportify = pyportify.server:main',
            'pyportify-copyall = pyportify.copy_all:main',
        ],
    },
    data_files=(
        ('', [
        "LICENSE.txt",
        ]),
    ),
    zip_safe=False,
    install_requires=install_requires,
)

if has_py2exe:
    args["console"] = "pyportify/server.py"

setup(**args)
