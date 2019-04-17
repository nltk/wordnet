
from wn.utils import WordNetObject

class Lemma(WordNetObject):
    def __init__(self, name, lexname_index, lex_id, syntactic_marker,
                 synset_offset=None, synset_pos=None,
                 synset_name=None, lemma_pointers=None):
        self._name = name
        self._syntactic_marker = syntactic_marker
        self._lexname_index = lexname_index
        self._lex_id = lex_id
        self._lang = 'eng'
        self._synset_offset = synset_offset
        self._synset_pos = synset_pos
        self._synset_name = synset_name
        self._lemma_pointers = lemma_pointers
        ##self._frame_strings = []
        ##self._frame_ids = []

    def name(self):
        return self._name

    def syntactic_marker(self):
        return self._syntactic_marker

    def synset(self):
        if hasattr(self, '_synset'):
            return self._synset
        else: # Fetch the synset from `_synset_offset_cache`
            self._synset = _synset_offset_cache[self._synset_pos][self._synset_offset]
        return self._synset

    def frame_strings(self):
        return self._frame_strings

    def frame_ids(self):
        return self._frame_ids

    def lang(self):
        return self._lang

    def key(self):
        return self._key

    def __repr__(self):
        tup = type(self).__name__, self._synset_name, self._name
        return "%s('%s.%s')" % tup

    def antonyms(self):
        return self._related('!')

    def derivationally_related_forms(self):
        return self._related('+')

    def pertainyms(self):
        return self._related('\\')

    def _related(self, relation_symbol):
        if (self._name, relation_symbol) not in self._lemma_pointers:
            return []
        return [
            _synset_offset_cache[pos][offset]._lemmas[lemma_index]
            for pos, offset, lemma_index in self._lemma_pointers[
                self._name, relation_symbol
            ]
        ]
