# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 NLTK Project
# Author:
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

"""
Tests for morphy.
"""

import unittest

from wn import WordNet

from wn.morphy import morphy

class TestMorphy(unittest.TestCase):
    def test_morphy(self):
        assert morphy('dogs') == 'dog'
        assert morphy('churches') == 'church'
        assert morphy('aardwolves') == 'aardwolf'
        assert morphy('abaci') == 'abacus'
        assert morphy('hardrock', 'r') == None
        assert morphy('book', 'n') == 'book'
        assert morphy('book', 'a') == None
