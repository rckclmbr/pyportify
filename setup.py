#!/usr/bin/env python3

from distutils.core import setup
from setuptools import find_packages
import os
import pathlib
import re

basepath = os.path.dirname(__file__)
requirements_txt = os.path.join(basepath, "requirements.txt")

with open(requirements_txt) as reqs:
    install_requires = [
        line for line in reqs.read().split('\n')
        if (line and not line.startswith('git+') and not line.startswith('--'))
        ]


def get_version(filename):
    with open(filename) as r:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", r.read()))
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
    long_description=pathlib.Path('README.md').read_text(),
    long_description_content_type='text/markdown', 
    classifiers=['Environment :: Web Environment'],
    entry_points={
        'console_scripts': ['pyportify = pyportify.server:main',
                            'pyportify-copyall = pyportify.copy_all:main']},
    data_files=(('', ["LICENSE.txt"]),),
    zip_safe=False,
    install_requires=install_requires)

setup(**args)
