
import os
from collections import defaultdict

from tqdm import tqdm
from lazyme import find_files

from wn.constants import *
from wn.constants import wordnet_dir
from wn.reader import parse_wordnet_line
from wn.reader import parse_index_line
from wn.reader import parse_lemma_pos_index
from wn.utils import WordNetError, FakeSynset

# Abusing builtins here but this is the only way I can think of.
# A index that provides the file offset
# Map from lemma -> pos -> synset_index -> offset
__builtins__['_lemma_pos_offset_map'] = defaultdict(dict)
# A cache so we don't have to reconstuct synsets
# Map from pos -> offset -> synset
__builtins__['_synset_offset_cache'] = defaultdict(dict)


class WordNet:
    def __init__(self):
        self._load_lemma_pos_offset_map()
        self._load_all_synsets()

        self._synset_offset_cache = _synset_offset_cache
        self._lemma_pos_offset_map = _lemma_pos_offset_map

    def _load_lemma_pos_offset_map(self):
        for pos_tag in _FILEMAP.values():
            filename = os.path.join(wordnet_dir, 'index.{}'.format(pos_tag))
            with open(filename) as fin:
                for line in fin:
                    if line.startswith(' '):
                        continue
                    lemma, pos, synset_offsets = parse_index_line(line)
                    # Cache the map.
                    _lemma_pos_offset_map[lemma][pos] = synset_offsets
                    if pos == 'a':
                        _lemma_pos_offset_map[lemma]['s'] = synset_offsets

    def _load_all_synsets(self):
        for pos_tag in _FILEMAP.values():
            filename = os.path.join(wordnet_dir, 'data.{}'.format(pos_tag))
            with open(filename) as fin:
                for line in tqdm(fin):
                    if line.startswith(' '):
                        continue
                    try:
                        synset, lemmas = parse_wordnet_line(line)
                        _synset_offset_cache[synset._pos][synset._offset] = synset
                    except:
                        err_msg = "Error parsing this line from {}:\n".format('data.{}'.format(pos_tag))
                        raise WordNetError(err_msg + line)

    def synset_from_pos_and_offset(self, pos, offset):
        assert pos in POS_LIST, WordNetError('Part-of-Speech should be one of this: {}'.format(POS_LIST))
        try:
            return _synset_offset_cache[pos][int(offset)]
        except:
            raise WordNetError('Part-of-Speech and Offset combination not found in WordNet: {} + {}'.format(pos, offset))

    def synset(self, lemma_pos_index):
        # Parse the lemma_pos_index string.
        pos, offset = parse_lemma_pos_index(lemma_pos_index)
        # load synset information from the appropriate file
        synset = self.synset_from_pos_and_offset(pos, offset)
        # Return the synset object.
        return synset

    def synsets(self, lemma, pos=None, lang='eng', check_exceptions=True):
        """
        Load all synsets with a given lemma and part of speech tag.
        If no pos is specified, all synsets for all parts of speech
        will be loaded.
        If lang is specified, all the synsets associated with the lemma name
        of that language will be returned.
        """
        lemma = lemma.lower()
        pos = POS_LIST if pos == None else pos
        if lang == 'eng':
            list_of_synsets = []
            for p in pos:
                for form in morphy(lemma, p, check_exceptions):
                    for offset in _lemma_pos_offset_map[form].get(p, []):
                        list_of_synsets.append(_synset_offset_cache[p][offset])
            return list_of_synsets

    def synset_from_sense_key(self, sense_key):
        pass

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
        synsets = synset1.common_hypernyms(synset2)
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


wordnet = WordNet()
