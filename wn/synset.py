
from collections import defaultdict

from wn.utils import WordNetObject

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
