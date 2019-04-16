

class _WordNetObject(object):
    """A common base class for lemmas and synsets."""

    def hypernyms(self):
        return self._related('@')

    def _hypernyms(self):
        return self._related('@')

    def instance_hypernyms(self):
        return self._related('@i')

    def _instance_hypernyms(self):
        return self._related('@i')

    def hyponyms(self):
        return self._related('~')

    def instance_hyponyms(self):
        return self._related('~i')

    def member_holonyms(self):
        return self._related('#m')

    def substance_holonyms(self):
        return self._related('#s')

    def part_holonyms(self):
        return self._related('#p')

    def member_meronyms(self):
        return self._related('%m')

    def substance_meronyms(self):
        return self._related('%s')

    def part_meronyms(self):
        return self._related('%p')

    def topic_domains(self):
        return self._related(';c')

    def in_topic_domains(self):
        return self._related('-c')

    def region_domains(self):
        return self._related(';r')

    def in_region_domains(self):
        return self._related('-r')

    def usage_domains(self):
        return self._related(';u')

    def in_usage_domains(self):
        return self._related('-u')

    def attributes(self):
        return self._related('=')

    def entailments(self):
        return self._related('*')

    def causes(self):
        return self._related('>')

    def also_sees(self):
        return self._related('^')

    def verb_groups(self):
        return self._related('$')

    def similar_tos(self):
        return self._related('&')

    def __hash__(self):
        return hash(self._name)

    def __eq__(self, other):
        return self._name == other._name

    def __ne__(self, other):
        return self._name != other._name

    def __lt__(self, other):
        return self._name < other._name

class Lemma:
    def __init__(self, name, lexname_index, lex_id, syntactic_marker,
                 synset_name=None, lemma_pointers=None):
        self._name = name
        self._syntactic_marker = syntactic_marker
        self._lexname_index = lexname_index
        self._lex_id = lex_id
        self._lang = 'eng'
        self._synset_name = synset_name
        self._lemma_pointers = None
        ##self._frame_strings = []
        ##self._frame_ids = []

    def name(self):
        return self._name

    def syntactic_marker(self):
        return self._syntactic_marker

    def synset(self):
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
            self._synset_offset_cache[pos][offset]._lemmas[lemma_index]
            for pos, offset, lemma_index in self._synset._lemma_pointers[
                self._name, relation_symbol
            ]
        ]
