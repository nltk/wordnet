# -*- coding: utf-8 -*-

import math
from itertools import chain
from operator import itemgetter
from collections import defaultdict

import wn.path
from wn.constants import *
from wn.lemma import Lemma
from wn.morphy import morphy
from wn.omw import OpenMultilingualWordNet as OMW
from wn.utils import WordNetObject, WordNetError
from wn.utils import breadth_first, FakeSynset

class Synset(WordNetObject):
    def __init__(self, offset, pos, name, lexname_index, lexname,
                 definition, examples=None, pointers=None,
                 lemmas=None, wordnet_line=None):

        self._offset = offset
        self._pos = pos
        self._name = name
        self._lexname = lexname  # lexicographer name.

        self._definition = definition
        self._examples = examples if examples else []

        self._pointers = pointers if pointers else defaultdict(set)
        self._lemmas = lemmas

        self._wordnet_line = wordnet_line

    def __repr__(self):
        return "%s('%s')" % (type(self).__name__, self._name)

    def offset(self):
        return self._offset

    def pos(self):
        return self._pos

    def name(self):
        return self._name

    def definition(self):
        return self._definition

    def examples(self):
        return self._examples

    def lexname(self):
        return self._lexname

    def _needs_root(self): # Assumes Wordnet >=V3.0.
        if self._pos == NOUN:
            return False
        elif self._pos == VERB:
            return True

    def lemmas(self, lang='eng'):
        '''Return all the lemma objects associated with the synset'''
        if lang == 'eng':
            return self._lemmas
        else:
            if lang not in _lang_to_lemmas_to_offsets.keys():
                # If not in cache, temporarily create an OMW object.
                # Get the mappings from the staticmethod `custom_lemmas()`
                offsets_to_lemmas, lemmas_to_offsets = OMW.custom_lemmas(lang)
                # Load it up.
                _lang_to_offsets_to_lemma[lang] = offsets_to_lemmas
                _lang_to_lemmas_to_offsets[lang] = lemmas_to_offsets
            # Return the list of lemmas from the OMW cache.
            lemmark = []
            for lemma_name in self.lemma_names(lang):
                _name = lemma_name
                _lexname_index = _lex_id = 0
                _syntactic_marker = None
                _synset_name = self._name
                _synset_offset = self._offset
                _synset_pos = self._pos
                lemma = Lemma(_name, _lexname_index, _lex_id, _syntactic_marker,
                              _synset_offset, _synset_pos, _synset_name,
                              lemma_pointers=None, lang=lang)
                lemmark.append(lemma)
            return lemmark

    def lemma_names(self, lang='eng'):
        if lang == 'eng':
            return [l._name for l in self._lemmas]
        else:
            if lang not in _lang_to_lemmas_to_offsets.keys():
                # If not in cache, temporarily create an OMW object.
                # Get the mappings from the staticmethod `custom_lemmas()`
                offsets_to_lemmas, lemmas_to_offsets = OMW.custom_lemmas(lang)
                # Load it up.
                _lang_to_offsets_to_lemma[lang] = offsets_to_lemmas
                _lang_to_lemmas_to_offsets[lang] = lemmas_to_offsets

            # Return the list of lemmas from the OMW cache.
            if self._pos in _lang_to_offsets_to_lemma[lang]:
                return _lang_to_offsets_to_lemma[lang][self._pos][self._offset]
            elif self._pos == 's' and 'a' in _lang_to_offsets_to_lemma[lang]:
                return _lang_to_offsets_to_lemma[lang]['a'][self._offset]
            else:
                return []

    def _related(self, relation_symbol, sort=True):
        if relation_symbol not in self._pointers:
            return []
        related_synsets = []
        for pos, offset in self._pointers[relation_symbol]:
            if pos in ['s', 'a']:
                try:
                    related_synset = _synset_offset_cache['a'][offset]
                except:
                    try:
                        related_synset = _synset_offset_cache['s'][offset]
                    except:
                        raise WordNetError('Part-of-Speech and Offset combination not found in WordNet: {} + {}'.format(pos, offset))
            else:
                related_synset = _synset_offset_cache[pos][offset]
            related_synsets.append(related_synset)

        return sorted(related_synsets) if sort else related_synsets

    def _hypernym_paths(self):
        """
        Get the path(s) from this synset to the root, where each path is a
        list of the synset nodes traversed on the way to the root.
        :return: A list of lists, where each list gives the node sequence
        connecting the initial ``Synset`` node and a root node.
        """
        paths = []
        hypernyms = self.hypernyms() + self.instance_hypernyms()
        if len(hypernyms) == 0:
            paths  = [[self]]
        for hypernym in hypernyms:
            for ancestor_list in hypernym._hypernym_paths():
                ancestor_list.append(self)
                paths.append(ancestor_list)
        return paths

    def _init_hypernym_paths(self):
        """
        Note: This can only be done after the whole wordnet is read, so
        this will be called on the fly when user tries to access:
        (i) _hyperpaths, (ii) _min_depth, (iii) _max_depth or (iv) _root_hypernyms
        """
        self._hyperpaths = self._hypernym_paths()
        # Compute the path related statistics.
        if self._hyperpaths:
            self._min_depth = min(len(path) for path in self._hyperpaths) - 1
            self._max_depth = max(len(path) for path in self._hyperpaths) - 1
        else:
            self._min_depth = self._max_depth = 0
        # Compute the store the root hypernyms.
        self._root_hypernyms = list(set([path[0] for path in self._hyperpaths]))
        # Initialize the hypernyms_set for `common_hypernyms()`
        self._hypernyms_set = set(chain(*self._hyperpaths))
        self._hypernyms_set.remove(self)

    def hypernym_paths(self):
        if not hasattr(self, '_hyperpaths'):
            self._init_hypernym_paths()
        return self._hyperpaths

    def min_depth(self):
        if not hasattr(self, '_min_depth'):
            self._init_hypernym_paths()
        return self._min_depth

    def max_depth(self):
        if not hasattr(self, '_max_depth'):
            self._init_hypernym_paths()
        return self._max_depth

    def root_hypernyms(self):
        if not hasattr(self, '_root_hypernyms'):
            self._init_hypernym_paths()
        return self._root_hypernyms

    def hypernyms_set(self):
        if not hasattr(self, '_hypernyms_set'):
            self._init_hypernym_paths()
        return self._hypernyms_set

    def closure(self, rel, depth=-1):
        """Return the transitive closure of source under the rel
        relationship, breadth-first
            >>> from nltk.corpus import wordnet as wn
            >>> dog = wn.synset('dog.n.01')
            >>> hyp = lambda s:s.hypernyms()
            >>> list(dog.closure(hyp))
            [Synset('canine.n.02'), Synset('domestic_animal.n.01'),
            Synset('carnivore.n.01'), Synset('animal.n.01'),
            Synset('placental.n.01'), Synset('organism.n.01'),
            Synset('mammal.n.01'), Synset('living_thing.n.01'),
            Synset('vertebrate.n.01'), Synset('whole.n.02'),
            Synset('chordate.n.01'), Synset('object.n.01'),
            Synset('physical_entity.n.01'), Synset('entity.n.01')]
        """
        synset_offsets = []
        for synset in breadth_first(self, rel, depth):
            if synset._offset != self._offset:
                if synset._offset not in synset_offsets:
                    synset_offsets.append(synset._offset)
                    yield synset

    def tree(self, rel, depth=-1, cut_mark=None):
        """
        >>> from nltk.corpus import wordnet as wn
        >>> dog = wn.synset('dog.n.01')
        >>> hyp = lambda s:s.hypernyms()
        >>> from pprint import pprint
        >>> pprint(dog.tree(hyp))
        [Synset('dog.n.01'),
         [Synset('canine.n.02'),
          [Synset('carnivore.n.01'),
           [Synset('placental.n.01'),
            [Synset('mammal.n.01'),
             [Synset('vertebrate.n.01'),
              [Synset('chordate.n.01'),
               [Synset('animal.n.01'),
                [Synset('organism.n.01'),
                 [Synset('living_thing.n.01'),
                  [Synset('whole.n.02'),
                   [Synset('object.n.01'),
                    [Synset('physical_entity.n.01'),
                     [Synset('entity.n.01')]]]]]]]]]]]]],
         [Synset('domestic_animal.n.01'),
          [Synset('animal.n.01'),
           [Synset('organism.n.01'),
            [Synset('living_thing.n.01'),
             [Synset('whole.n.02'),
              [Synset('object.n.01'),
               [Synset('physical_entity.n.01'), [Synset('entity.n.01')]]]]]]]]]
        """
        tree = [self]
        if depth != 0:
            tree += [x.tree(rel, depth - 1, cut_mark) for x in rel(self)]
        elif cut_mark:
            tree += [cut_mark]
        return tree

    def hypernym_distances(self, distance=0, simulate_root=False):
        """
        Get the path(s) from this synset to the root, counting the distance
        of each node from the initial node on the way. A set of
        (synset, distance) tuples is returned.
        :type distance: int
        :param distance: the distance (number of edges) from this hypernym to
        the original hypernym ``Synset`` on which this method was called.
        :return: A set of ``(Synset, int)`` tuples where each ``Synset`` is
        a hypernym of the first ``Synset``.
        """
        distances = set([(self, distance)])
        for hypernym in self._hypernyms() + self._instance_hypernyms():
            distances |= hypernym.hypernym_distances(distance + 1, simulate_root=False)
        if simulate_root:
            fake_synset = FakeSynset(None)
            fake_synset._name = '*ROOT*'
            fake_synset_distance = max(distances, key=itemgetter(1))[1]
            distances.add((fake_synset, fake_synset_distance + 1))
        return distances
