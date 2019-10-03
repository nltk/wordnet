# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 NLTK Project
# Author:
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

"""
Tests for Synset and Lemma objects.
"""

import unittest

from wn import WordNet
from wn.info import WordNetInformationContent

from wn.constants import wordnet_30_dir

our_wn = WordNet(wordnet_30_dir)

class TestAllSynsets(unittest.TestCase):
    ##@unittest.skip("Paranoid sanity checks...")
    def test_all_synsets(self):
        from nltk.corpus import wordnet as nltk_wn
        our_wn_synsets = our_wn.all_synsets()
        for nltk_ss in nltk_wn.all_synsets():
            our_ss = our_wn.synset(nltk_ss.name())
            # Test Synset attributes.
            assert nltk_ss.name() == our_ss.name()
            assert nltk_ss.offset() == our_ss.offset()
            assert nltk_ss.pos() == our_ss.pos()
            assert nltk_ss.lexname() == our_ss.lexname()
            assert nltk_ss._needs_root() == our_ss._needs_root()

            # These two attributes are wrong in NLTK <= 3.4.1.
            ##assert nltk_ss.definition() == our_ss.definition()
            ##assert nltk_ss.examples() == our_ss.examples()

            # Check hypernym_paths()
            our_paths = [[ss.name() for ss in path]
                         for path in our_ss.hypernym_paths()]
            nltk_paths = [[ss.name() for ss in path]
                         for path in nltk_ss.hypernym_paths()]
            assert our_paths == nltk_paths

            # Check hypernym depths.
            assert our_ss.min_depth() == nltk_ss.min_depth()
            assert our_ss.max_depth() == nltk_ss.max_depth()

            # Check root_hypernyms.
            our_roots = [[ss.name() for ss in path]
                         for path in our_ss.hypernym_paths()]
            nltk_roots = [[ss.name() for ss in path]
                         for path in nltk_ss.hypernym_paths()]
            assert our_roots == nltk_roots

            # Check hypernym to root distances
            for simulate_root in [True, False]:
                our_hyperdist = [(hyper._name, dist) for hyper, dist
                    in our_ss.hypernym_distances(simulate_root=simulate_root)]
                nltk_hyperdist = [(hyper._name, dist) for hyper, dist
                    in nltk_ss.hypernym_distances(simulate_root=simulate_root)]
                assert sorted(our_hyperdist) == sorted(nltk_hyperdist)

            # Test Synset's lemma_names.
            assert sorted(nltk_ss.lemma_names()) == sorted(our_ss.lemma_names())

            # Test Synset's lemmas.
            for our_lemma, nltk_lemma in zip(sorted(our_ss.lemmas()), sorted(nltk_ss.lemmas())):
                assert our_lemma._name == nltk_lemma._name
                assert our_lemma._lexname_index == nltk_lemma._lexname_index
                assert our_lemma._lex_id == nltk_lemma._lex_id
                assert our_lemma._syntactic_marker == nltk_lemma._syntactic_marker

                assert our_lemma._synset_name == nltk_lemma.synset()._name
                assert our_lemma._synset_offset == nltk_lemma.synset()._offset
                assert our_lemma._synset_pos == nltk_lemma.synset()._pos

                assert our_lemma._lang == nltk_lemma._lang
                assert our_lemma.key() == nltk_lemma.key()

            # Test synset relations.
            assert our_ss._pointers == nltk_ss._pointers

    def test_synsets_similarities(self):
        from nltk.corpus import wordnet as nltk_wn
        nltk_car = nltk_wn.synset('car.n.1')
        nltk_bus = nltk_wn.synset('bus.n.1')

        our_car = our_wn.synset('car.n.1')
        our_bus = our_wn.synset('bus.n.1')

        # Hypernym paths.
        assert sorted(our_wn.common_hypernyms(our_car, our_bus)) == sorted(nltk_car.common_hypernyms(nltk_bus))
        assert our_wn.shortest_path_distance(our_car, our_bus, simulate_root=True) == nltk_car.shortest_path_distance(nltk_bus, simulate_root=True)
        assert our_wn.shortest_path_distance(our_car, our_bus, simulate_root=False) == nltk_car.shortest_path_distance(nltk_bus, simulate_root=False)

        # Path similarities.
        assert our_wn.path_similarity(our_car, our_bus) == nltk_car.path_similarity(nltk_bus)
        assert our_wn.wup_similarity(our_car, our_bus) == nltk_car.wup_similarity(nltk_bus)
        assert our_wn.lch_similarity(our_car, our_bus) == nltk_car.lch_similarity(nltk_bus)

    def test_wordnet_ic(self):
        from nltk.corpus import wordnet as nltk_wn
        from nltk.corpus import wordnet_ic as nltk_wnic
        nltk_car = nltk_wn.synset('car.n.1')
        nltk_bus = nltk_wn.synset('bus.n.1')
        our_bnc_resnik_add1 = WordNetInformationContent('bnc', resnik=True, add1=True)

        our_car = our_wn.synset('car.n.1')
        our_bus = our_wn.synset('bus.n.1')
        nltk_bnc_resnik_add1 = nltk_wnic.ic('ic-bnc-resnik-add1.dat')
        assert our_wn.res_similarity(our_car, our_bus, our_bnc_resnik_add1) == nltk_wn.res_similarity(nltk_car, nltk_bus, nltk_bnc_resnik_add1)
        assert our_wn.jcn_similarity(our_car, our_bus, our_bnc_resnik_add1) == nltk_wn.jcn_similarity(nltk_car, nltk_bus, nltk_bnc_resnik_add1)
        assert our_wn.lin_similarity(our_car, our_bus, our_bnc_resnik_add1) == nltk_wn.lin_similarity(nltk_car, nltk_bus, nltk_bnc_resnik_add1)
