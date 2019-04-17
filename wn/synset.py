
from collections import defaultdict

from wn.constants import *
from wn.utils import WordNetObject, WordNetError

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
