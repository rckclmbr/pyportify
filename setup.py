#!/usr/bin/env python3

from distutils.core import setup
from setuptools import find_packages
import os
import re

basepath = os.path.dirname(__file__)
readme_rst = os.path.join(basepath, "README.md")
requirements_txt = os.path.join(basepath, "requirements.txt")

with open(readme_rst) as readme:
    long_description = readme.read()

with open(requirements_txt) as reqs:
    install_requires = [
        line for line in reqs.read().split('\n') \
            if (line and
                   not line.startswith('git+') and
                   not line.startswith('--')
               )
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
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
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

setup(**args)
