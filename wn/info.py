# -*- coding: utf-8 -*-

import math
from collections import defaultdict

from wn.constants import wordnet_ic_dir
from wn.reader import parse_wordnet_ic_line
from wn.utils import WordNetError


class WordNetInformationContent:
    def __init__(self, corpus, resnik=False, add1=False):
        self.available_corpora = ['bnc', 'brown', 'semcor',
                                  'semcorraw', 'shak', 'treebank']
        if corpus not in self.available_corpora:
            msg = '{} not in list of availabel Wordnet IC files: {}'.format(self.available_corpora)
            raise WordNetError(msg)

        self.corpus = corpus
        self.with_resnik = '-resnik' if resnik else ''
        self.with_add1 = '-add1' if add1 else ''
        self.ic_filename = '/ic-{}{}{}.dat'.format(self.corpus,
                                                self.with_resnik,
                                                self.with_add1)

        self.ic = defaultdict(dict)
        with open(wordnet_ic_dir + self.ic_filename) as fin:
            next(fin) # Skip the first line.
            for line in fin:
                offset, value, pos, has_root = parse_wordnet_ic_line(line)
                if has_root:
                    self.ic[pos][0] = self.ic[pos].get(0, 0) + value
                if value != 0:
                    self.ic[pos][offset] = value


class InformationContentSimilarities:
    def information_content(self, synset, ic):
        if synset._pos in ic.ic and ic.ic[synset._pos]:
            icpos = ic.ic[synset._pos]
        else:
            msg = 'Information content file has no entries for part-of-speech: %s'
            raise WordNetError(msg % synset._pos)
        counts = icpos[synset._offset]
        if counts == 0:
            return _INF
        else:
            return -math.log(counts / icpos[0])

    def _lcs_ic(self, synset1, synset2, ic):
        """
        Get the information content of the least common subsumer that has
        the highest information content value.  If two nodes have no
        explicit common subsumer, assume that they share an artificial
        root node that is the hypernym of all explicit roots.
        :type synset1: Synset
        :param synset1: First input synset.
        :type synset2: Synset
        :param synset2: Second input synset.  Must be the same part of
        speech as the first synset.
        :type  ic: dict
        :param ic: an information content object (as returned by ``load_ic()``).
        :return: The information content of the two synsets and their most
        informative subsumer
        """
        if synset1._pos != synset2._pos:
            raise WordNetError(
                'Computing the least common subsumer requires '
                '%s and %s to have the same part of speech.' % (synset1, synset2)
            )

        ic1 = self.information_content(synset1, ic)
        ic2 = self.information_content(synset2, ic)
        # Find common hypernyms of synset1 and synset2
        subsumers = list(synset1.hypernyms_set().intersection(synset2.hypernyms_set()))
        if len(subsumers) == 0:
            subsumer_ic = 0
        else:
            subsumer_ic = max(self.information_content(s, ic) for s in subsumers)

        return ic1, ic2, subsumer_ic

    def res_similarity(self, synset1, synset2, ic):
        """
        Resnik Similarity:
        Return a score denoting how similar two word senses are, based on the
        Information Content (IC) of the Least Common Subsumer (most specific
        ancestor node).
        :type  other: Synset
        :param other: The ``Synset`` that this ``Synset`` is being compared to.
        :type ic: dict
        :param ic: an information content object (as returned by
        ``nltk.corpus.wordnet_ic.ic()``).
        :return: A float score denoting the similarity of the two ``Synset``
        objects. Synsets whose LCS is the root node of the taxonomy will
        have a score of 0 (e.g. N['dog'][0] and N['table'][0]).
        """
        ic1, ic2, lcs_ic = self._lcs_ic(synset1, synset2, ic)
        return lcs_ic

    def jcn_similarity(self, synset1, synset2, ic):
        """
        Jiang-Conrath Similarity:
        Return a score denoting how similar two word senses are, based on the
        Information Content (IC) of the Least Common Subsumer (most specific
        ancestor node) and that of the two input Synsets. The relationship is
        given by the equation 1 / (IC(s1) + IC(s2) - 2 * IC(lcs)).
        :type  other: Synset
        :param other: The ``Synset`` that this ``Synset`` is being compared to.
        :type  ic: dict
        :param ic: an information content object (as returned by
        ``nltk.corpus.wordnet_ic.ic()``).
        :return: A float score denoting the similarity of the two ``Synset``
        objects.
        """

        if synset1 == synset2:
            return _INF

        ic1, ic2, lcs_ic = self._lcs_ic(synset1, synset2, ic)

        # If either of the input synsets are the root synset, or have a
        # frequency of 0 (sparse data problem), return 0.
        if ic1 == 0 or ic2 == 0:
            return 0

        ic_difference = ic1 + ic2 - 2 * lcs_ic

        if ic_difference == 0:
            return _INF

        return 1 / ic_difference

    def lin_similarity(self, synset1, synset2, ic):
        """
        Lin Similarity:
        Return a score denoting how similar two word senses are, based on the
        Information Content (IC) of the Least Common Subsumer (most specific
        ancestor node) and that of the two input Synsets. The relationship is
        given by the equation 2 * IC(lcs) / (IC(s1) + IC(s2)).
        :type other: Synset
        :param other: The ``Synset`` that this ``Synset`` is being compared to.
        :type ic: dict
        :param ic: an information content object (as returned by
        ``nltk.corpus.wordnet_ic.ic()``).
        :return: A float score denoting the similarity of the two ``Synset``
        objects, in the range 0 to 1.
        """

        ic1, ic2, lcs_ic = self._lcs_ic(synset1, synset2, ic)
        return (2.0 * lcs_ic) / (ic1 + ic2)
