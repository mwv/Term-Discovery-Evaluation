#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='term-discovery-evaluation',
    version='0.1.0',
    description='Evaluation methods for word segmentation and spoken term discovery.',
    long_description=readme + '\n\n' + history,
    author='Maarten Versteegh',
    author_email='maartenversteegh@gmail.com',
    url='https://github.com/mwv/term-discovery-evaluation',
    packages=[
        'term-discovery-evaluation',
    ],
    package_dir={'term-discovery-evaluation': 'term-discovery-evaluation'},
    include_package_data=True,
    install_requires=[
    ],
    license="GPLv3",
    zip_safe=False,
    keywords='term-discovery-evaluation',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
)