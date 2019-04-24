# -*- coding: utf-8 -*-

from collections import deque

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

class WordNetError(Exception):
    """An exception class for wordnet-related errors."""

class FakeSynset:
    def __init__(self, name):
        self._name = '*ROOT*'
        self._min_depth = self._max_depth = 0
        self.hypernyms = lambda: []
        self.instance_hypernyms = lambda: []

    def min_depth(self):
        return self._min_depth

    def max_depth(self):
        return self._max_depth

    def __repr__(self):
        return "%s('%s')" % (type(self).__name__, self._name)

    def __hash__(self):
        return hash(self._name)

    def __eq__(self, other):
        return self._name == other._name

    def __ne__(self, other):
        return self._name != other._name

    def __lt__(self, other):
        return self._name < other._name

class WordNetObject(object):
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


def breadth_first(tree, children=iter, maxdepth=-1):
    """Traverse the nodes of a tree in breadth-first order.
    (No need to check for cycles.)
    The first argument should be the tree root;
    children should be a function taking as argument a tree node
    and returning an iterator of the node's children.
    """
    queue = deque([(tree, 0)])

    while queue:
        node, depth = queue.popleft()
        yield node

        if depth != maxdepth:
            try:
                queue.extend((c, depth + 1) for c in children(node))
            except TypeError:
                pass


def per_chunk(iterable, n=1, fillvalue=None):
    """
    From http://stackoverflow.com/a/8991553/610569
        >>> list(per_chunk('abcdefghi', n=2))
        [('a', 'b'), ('c', 'd'), ('e', 'f'), ('g', 'h'), ('i', None)]
        >>> list(per_chunk('abcdefghi', n=3))
        [('a', 'b', 'c'), ('d', 'e', 'f'), ('g', 'h', 'i')]
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)
