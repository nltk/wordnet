# -*- coding: utf-8 -*-

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
