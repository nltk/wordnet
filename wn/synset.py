
from collections import defaultdict

class Synset:
    def __init__(self, offset, pos, name, lexname_index, lexname,
                 definition, examples=None, pointers=None,
                 lemmas=None):

        self._offset = offset
        self._pos = pos
        self._name = name
        self._lexname = lexname  # lexicographer name.

        self._definition = definition
        self._examples = examples if examples else []

        self._pointers = pointers if pointers else defaultdict(set)
        self._lemmas = lemmas
