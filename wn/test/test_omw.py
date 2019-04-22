# -*- coding: utf-8 -*-

"""
Tests for OMW lemmas.
"""

import unittest

from wn import wordnet as our_wn


class TestOMWLemmas(unittest.TestCase):
    def test_all_lemma_names(self):
        from nltk.corpus import wordnet as nltk_wn
        our_wn_synsets = our_wn.all_synsets()
        for nltk_ss in nltk_wn.all_synsets():
            our_ss = our_wn.synset(nltk_ss.name())
            for lang in our_wn.langs():
                our_lemma_names = sorted([l for l in our_ss.lemma_names(lang=lang)])
                # Note: https://github.com/nltk/nltk/issues/2275
                nltk_lemma_names = sorted([l.strip('_') for l in nltk_ss.lemma_names(lang=lang)])
                assert our_lemma_names == nltk_lemma_names
