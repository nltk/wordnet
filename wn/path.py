# -*- coding: utf-8 -*-

import math
from collections import deque

from wn.utils import FakeSynset, WordNetError
from wn.constants import WN_MAX_DEPTH

def find_root_hypernyms(synset):
    """
    Note: Not used anywhere in this library, keeping it for reference to NLTK.
    Get the topmost hypernyms of this synset in WordNet.
    """
    result = []
    seen = set()
    todo = [synset]
    max_depth, min_depth
    while todo:
        next_synset = todo.pop()
        if next_synset not in seen:
            seen.add(next_synset)
            next_hypernyms = (
                next_synset.hypernyms() + next_synset.instance_hypernyms()
            )
            if not next_hypernyms:
                result.append(next_synset)
            else:
                todo.extend(next_hypernyms)
    return result

def find_shortest_hypernym_paths_to_root(synset, simulate_root=False):
    if synset._name == '*ROOT*':
        return {synset: 0}

    queue = deque([(synset, 0)])
    path = {}

    while queue:
        s, depth = queue.popleft()
        if s in path:
            continue
        path[s] = depth
        depth += 1
        queue.extend((hyp, depth) for hyp in s._hypernyms())
        queue.extend((hyp, depth) for hyp in s._instance_hypernyms())

    if simulate_root:
        fake_synset = FakeSynset(None)
        fake_synset._name = '*ROOT*'
        path[fake_synset] = max(path.values()) + 1

    return path


class WordNetPaths:
    def common_hypernyms(self, synset1, synset2):
        """
        Find all synsets that are hypernyms of this synset and the
        other synset.
        :return: The synsets that are hypernyms of both synsets.
        """
        return list(synset1.hypernyms_set().intersection(synset2.hypernyms_set()))

    def lowest_common_hypernyms(self, synset1, synset2,
                                simulate_root=False, use_min_depth=False):
        """
        Get a list of lowest synset(s) that both synsets have as a hypernym.
        When `use_min_depth == False` this means that the synset which appears
        as a hypernym of both `self` and `other` with the lowest maximum depth
        is returned or if there are multiple such synsets at the same depth
        they are all returned
        However, if `use_min_depth == True` then the synset(s) which has/have
        the lowest minimum depth and appear(s) in both paths is/are returned.
        By setting the use_min_depth flag to True, the behavior of NLTK2 can be
        preserved. This was changed in NLTK3 to give more accurate results in a
        small set of cases, generally with synsets concerning people. (eg:
        'chef.n.01', 'fireman.n.01', etc.)
        This method is an implementation of Ted Pedersen's "Lowest Common
        Subsumer" method from the Perl Wordnet module. It can return either
        "self" or "other" if they are a hypernym of the other.
        :type other: Synset
        :param other: other input synset
        :type simulate_root: bool
        :param simulate_root: The various verb taxonomies do not
            share a single root which disallows this metric from working for
            synsets that are not connected. This flag (False by default)
            creates a fake root that connects all the taxonomies. Set it
            to True to enable this behavior. For the noun taxonomy,
            there is usually a default root except for WordNet version 1.6.
            If you are using wordnet 1.6, a fake root will need to be added
            for nouns as well.
        :type use_min_depth: bool
        :param use_min_depth: This setting mimics older (v2) behavior of NLTK
            wordnet If True, will use the min_depth function to calculate the
            lowest common hypernyms. This is known to give strange results for
            some synset pairs (eg: 'chef.n.01', 'fireman.n.01') but is retained
            for backwards compatibility
        :return: The synsets that are the lowest common hypernyms of both
            synsets
        """
        synsets = self.common_hypernyms(synset1, synset2)
        if simulate_root:
            fake_synset = FakeSynset(None)
            fake_synset._name = '*ROOT*'
            fake_synset.hypernyms = lambda: []
            fake_synset.instance_hypernyms = lambda: []
            synsets.append(fake_synset)

        try:
            if use_min_depth:
                max_depth = max(s.min_depth() for s in synsets)
                unsorted_lch = [s for s in synsets if s.min_depth() == max_depth]
            else:
                max_depth = max(s.max_depth() for s in synsets)
                unsorted_lch = [s for s in synsets if s.max_depth() == max_depth]
            return sorted(unsorted_lch)
        except ValueError:
            return []

    def shortest_path_distance(self, synset1, synset2, simulate_root=False):
        """
        Returns the distance of the shortest path linking the two synsets (if
        one exists). For each synset, all the ancestor nodes and their
        distances are recorded and compared. The ancestor node common to both
        synsets that can be reached with the minimum number of traversals is
        used. If no ancestor nodes are common, None is returned. If a node is
        compared with itself 0 is returned.
        :type other: Synset
        :param other: The Synset to which the shortest path will be found.
        :return: The number of edges in the shortest path connecting the two
        nodes, or None if no path exists.
        """
        if synset1 == synset2:
            return 0
        # Find the shortest hypernym path to *ROOT*
        dist_dict1 = find_shortest_hypernym_paths_to_root(synset1, simulate_root)
        dist_dict2 = find_shortest_hypernym_paths_to_root(synset2, simulate_root)
        # For each ancestor synset common to both subject synsets, find the
        # connecting path length. Return the shortest of these.
        inf = float('inf')
        path_distance = inf
        for synset, d1 in dist_dict1.items():
            d2 = dist_dict2.get(synset, inf)
            path_distance = min(path_distance, d1 + d2)
        return None if math.isinf(path_distance) else path_distance

    def path_similarity(self, synset1, synset2, verbose=False, simulate_root=True,
                        if_none_return=None):
        """
        Path Distance Similarity:
        Return a score denoting how similar two word senses are, based on the
        shortest path that connects the senses in the is-a (hypernym/hypnoym)
        taxonomy. The score is in the range 0 to 1, except in those cases where
        a path cannot be found (will only be true for verbs as there are many
        distinct verb taxonomies), in which case None is returned. A score of
        1 represents identity i.e. comparing a sense with itself will return 1.
        :type other: Synset
        :param other: The ``Synset`` that this ``Synset`` is being compared to.
        :type simulate_root: bool
        :param simulate_root: The various verb taxonomies do not
        share a single root which disallows this metric from working for
        synsets that are not connected. This flag (True by default)
        creates a fake root that connects all the taxonomies. Set it
        to false to disable this behavior. For the noun taxonomy,
        there is usually a default root except for WordNet version 1.6.
        If you are using wordnet 1.6, a fake root will be added for nouns
        as well.
        :return: A score denoting the similarity of the two ``Synset`` objects,
        normally between 0 and 1. None is returned if no connecting path
        could be found. 1 is returned if a ``Synset`` is compared with
        itself.
        """
        distance = self.shortest_path_distance(synset1, synset2,
            simulate_root=simulate_root and synset1._needs_root())
        if distance is None or distance < 0:
            return if_none_return
        return 1.0 / (distance + 1)

    def _compute_max_depth(self, pos, simulate_root):
        """
        Compute the max depth for the given part of speech.  This is
        used by the lch similarity metric.
        """
        depth = 0
        for ii in self.all_synsets(pos):
            try:
                depth = max(depth, ii.max_depth())
            except RuntimeError:
                print(ii)
        if simulate_root:
            depth += 1
        self._max_depth[pos] = depth

    def lch_similarity(self, synset1, synset2,
                       simulate_root=True, _max_depth=None,
                       if_none_return=None):
        """
        Leacock Chodorow Similarity:
        Return a score denoting how similar two word senses are, based on the
        shortest path that connects the senses (as above) and the maximum depth
        of the taxonomy in which the senses occur. The relationship is given as
        -log(p/2d) where p is the shortest path length and d is the taxonomy
        depth.
        :type  other: Synset
        :param other: The ``Synset`` that this ``Synset`` is being compared to.
        :type simulate_root: bool
        :param simulate_root: The various verb taxonomies do not
            share a single root which disallows this metric from working for
            synsets that are not connected. This flag (True by default)
            creates a fake root that connects all the taxonomies. Set it
            to false to disable this behavior. For the noun taxonomy,
            there is usually a default root except for WordNet version 1.6.
            If you are using wordnet 1.6, a fake root will be added for nouns
            as well.
        :return: A score denoting the similarity of the two ``Synset`` objects,
            normally greater than 0. None is returned if no connecting path
            could be found. If a ``Synset`` is compared with itself, the
            maximum score is returned, which varies depending on the taxonomy
            depth.
        """

        if synset1._pos != synset2._pos:
            raise WordNetError(
                'Computing the lch similarity requires '
                '%s and %s to have the same part of speech.' % (synset1, synset2)
            )

        # Note the s`imlulate_root` here only tries to simulate
        # Ultimately the synset's need_root and simulate_root decides
        # whether root is really needed
        need_root = synset1._needs_root() and simulate_root
        # Hack to handle adjective and adverbs where _needs_root() returns None.
        if need_root == None:
            if if_none_return:
                need_root = True
            else: # Emulate NLTK's behavior to return None.
                return if_none_return
        # FIXME: how to make subclass overwrite values in kwargs?
        # By default use the static value from wn.constants
        depth = _max_depth if _max_depth else WN_MAX_DEPTH['3.0'][need_root][synset1._pos]
        distance = self.shortest_path_distance(synset1, synset2,
                        simulate_root=need_root)

        if distance is None or distance < 0 or depth == 0:
            return if_none_return
        return -math.log((distance + 1) / (2.0 * depth))

    def wup_similarity(self, synset1, synset2,
                       verbose=False, simulate_root=True,
                       if_none_return=None):
        """
        Wu-Palmer Similarity:
        Return a score denoting how similar two word senses are, based on the
        depth of the two senses in the taxonomy and that of their Least Common
        Subsumer (most specific ancestor node). Previously, the scores computed
        by this implementation did _not_ always agree with those given by
        Pedersen's Perl implementation of WordNet Similarity. However, with
        the addition of the simulate_root flag (see below), the score for
        verbs now almost always agree but not always for nouns.
        The LCS does not necessarily feature in the shortest path connecting
        the two senses, as it is by definition the common ancestor deepest in
        the taxonomy, not closest to the two senses. Typically, however, it
        will so feature. Where multiple candidates for the LCS exist, that
        whose shortest path to the root node is the longest will be selected.
        Where the LCS has multiple paths to the root, the longer path is used
        for the purposes of the calculation.
        :type  other: Synset
        :param other: The ``Synset`` that this ``Synset`` is being compared to.
        :type simulate_root: bool
        :param simulate_root: The various verb taxonomies do not
        share a single root which disallows this metric from working for
        synsets that are not connected. This flag (True by default)
        creates a fake root that connects all the taxonomies. Set it
        to false to disable this behavior. For the noun taxonomy,
        there is usually a default root except for WordNet version 1.6.
        If you are using wordnet 1.6, a fake root will be added for nouns
        as well.
        :return: A float score denoting the similarity of the two ``Synset``
        objects, normally greater than zero. If no connecting path between
        the two senses can be found, None is returned.
        """

        # Note the s`imlulate_root` here only tries to simulate
        # Ultimately the synset's need_root and simulate_root decides
        # whether root is really needed
        need_root = synset1._needs_root() and simulate_root
        # Note that to preserve behavior from NLTK2 we set use_min_depth=True
        # It is possible that more accurate results could be obtained by
        # removing this setting and it should be tested later on
        subsumers = self.lowest_common_hypernyms(synset1, synset2,
                        simulate_root=need_root, use_min_depth=True)

        # If no LCS was found return None
        if len(subsumers) == 0:
            return if_none_return

        subsumer = synset1 if synset1 in subsumers else subsumers[0]

        # Get the longest path from the LCS to the root,
        # including a correction:
        # - add one because the calculations include both the start and end
        #   nodes
        depth = subsumer.max_depth() + 1

        # Note: No need for an additional add-one correction for non-nouns
        # to account for an imaginary root node because that is now
        # automatically handled by simulate_root
        # if subsumer._pos != NOUN:
        #     depth += 1

        # Get the shortest path from the LCS to each of the synsets it is
        # subsuming.  Add this to the LCS path length to get the path
        # length from each synset to the root.
        len1 = self.shortest_path_distance(synset1, subsumer,
                simulate_root=simulate_root and need_root)
        len2 = self.shortest_path_distance(synset2, subsumer,
                simulate_root=simulate_root and need_root)
        if len1 is None or len2 is None:
            return if_none_return
        len1 += depth
        len2 += depth
        return (2.0 * depth) / (len1 + len2)
