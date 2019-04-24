# -*- coding: utf-8 -*-

"""
Tests for OMW lemmas.
"""

import unittest

from wn import WordNet

our_wn = WordNet()

class TestSimilarities(unittest.TestCase):
    def test_path_similarities_simulate_root(self):
        from nltk.corpus import wordnet as nltk_wn
        nltk_run = nltk_wn.synset('run.v.1')
        nltk_dog = nltk_wn.synset('dog.n.1')


        our_run = wn.synset('run.v.1')
        our_dog = wn.synset('dog.n.1')

        assert nltk_wn.path_similarity(nltk_run, nltk_dog) ==  our_wn.path_similarity(our_run, our_dog)
        assert nltk_wn.wup_similarity(nltk_run, nltk_dog) ==  our_wn.wup_similarity(our_run, our_dog)

    def test_path_commutative(self):
        # Note: Path similarities are not commutative.
        from nltk.corpus import wordnet as nltk_wn
        nltk_cat = nltk_wn.synset('cat.n.01')
        nltk_buy = nltk_wn.synset('buy.v.01')

        our_cat = wn.synset('cat.v.1')
        our_buy = wn.synset('buy.n.1')
        # path_sim(cat, buy)
        assert nltk_wn.path_similarity(nltk_cat, nltk_buy) ==  our_wn.path_similarity(our_cat, our_buy)
        assert nltk_wn.wup_similarity(nltk_cat, nltk_buy) ==  our_wn.wup_similarity(our_cat, our_buy)
        # path_sim(buy, sim)
        assert nltk_wn.path_similarity(nltk_buy, nltk_cat) ==  our_wn.path_similarity(our_buy, our_cat)
        assert nltk_wn.wup_similarity(nltk_buy, nltk_cat) ==  our_wn.wup_similarity(our_buy, our_cat)

    def test_path_similarities(self):
        from nltk.corpus import wordnet as nltk_wn
        nltk_cat = nltk_wn.synset('cat.n.1')
        nltk_dog = nltk_wn.synset('dog.n.1')
        nltk_bus = nltk_wn.synset('bus.n.1')

        our_cat = wn.synset('cat.n.1')
        our_dog = wn.synset('dog.n.1')
        our_bus = wn.synset('bus.n.1')
        assert nltk_wn.path_similarity(nltk_cat, nltk_dog) ==  our_wn.path_similarity(our_cat, our_dog)
        assert nltk_wn.wup_similarity(nltk_cat, nltk_dog) ==  our_wn.wup_similarity(our_cat, our_dog)
        assert nltk_wn.lch_similarity(nltk_cat, nltk_dog) ==  our_wn.lch_similarity(our_cat, our_dog)

        assert nltk_wn.path_similarity(nltk_cat, nltk_bus) ==  our_wn.path_similarity(our_cat, our_bus)
        assert nltk_wn.wup_similarity(nltk_cat, nltk_bus) ==  our_wn.wup_similarity(our_cat, our_bus)
        assert nltk_wn.lch_similarity(nltk_cat, nltk_bus) ==  our_wn.lch_similarity(our_cat, our_bus)
