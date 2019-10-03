#!/usr/bin/env python
#
# Setup script for Standalone WordNet API
#
# Copyright (C) 2019-2020 NLTK Project
# Author:
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

from distutils.core import setup

setup(
    name='wn',
    version='0.0.22',
    packages=['wn'],
    description='Wordnet',
    long_description='',
    url = 'https://github.com/nltk/wordnet',
    package_data={'wn': ['data/omw/*',
                         'data/wordnet-3.0/*',
                         'data/wordnet-3.3/*',
                         'data/wordnet_ic/*',]},
    license="Apache License, Version 2.0"
)
