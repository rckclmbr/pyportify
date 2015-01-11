#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages

with open('README.md') as readme:
    long_description = readme.read()

with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n') if (line and not
                                                     line.startswith('--'))
    ]

setup(
    name='pyportify',
    version="0.1.1",
    author='Josh Braegger',
    author_email='rckclmbr@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/rckclmbr/pyportify',
    license='BSD',
    description='Django app to transfer your spotify playlists to Google Play '
                'Music',
    long_description=long_description,
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
    ],
    entry_points={
        'console_scripts': [
            'pyportify = pyportify.server:main',
            'pyportify-copyall = pyportify.copy_all:main',
        ],
    },
    data_files=(
        ('', [
        "LICENSE",
        "README.md",
        ]),
    ),
    zip_safe=False,
    install_requires=install_requires,
)
