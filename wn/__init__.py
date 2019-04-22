
import os
import re
from collections import defaultdict

from tqdm import tqdm
from lazyme import find_files

from wn.constants import *
from wn.path import WordNetPaths
from wn.reader import parse_wordnet_line
from wn.reader import parse_index_line
from wn.reader import parse_lemma_pos_index
from wn.reader import parse_sense_key
from wn.utils import WordNetError, FakeSynset

from wn.info import WordNetInformationContent

# Abusing builtins here but this is the only way I can think of.
# A index that provides the file offset
# Map from lemma -> pos -> synset_index -> offset
__builtins__['_lemma_pos_offset_map'] = defaultdict(dict)
# A cache so we don't have to reconstuct synsets
# Map from pos -> offset -> synset
__builtins__['_synset_offset_cache'] = defaultdict(dict)


class WordNet(WordNetPaths):
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
        lemma, pos, lex_id = parse_sense_key(sense_key)
        synset_id = '.'.join([lemma, pos, lex_id])
        return self.synset(synset_id)

    def all_synsets(self, pos=None):
        """Iterate over all synsets with a given part of speech tag.
        If no pos is specified, all synsets for all parts of speech
        will be loaded.
        """
        pos_tags = _FILEMAP.keys() if pos is None else [pos]

        for _pos in pos_tags:
            for offset, ss in _synset_offset_cache[_pos].items():
                yield ss

    def all_lemma_names(self, pos=None, lang='eng'):
        if lang == 'eng':
            if pos is None:
                for lemma_name in _lemma_pos_offset_map:
                    if pos in _lemma_pos_offset_map[lemma]:
                        yield lemma_name

    def words(self, lang='lang'):
        """return lemmas of the given language as list of words"""
        return self.all_lemma_names(lang=lang)

    def _compute_max_depth_once(self, pos, simulate_root):
        """
        Compute the max depth for the given part of speech.  This is
        used by the lch similarity metric.

        This function should never be used!!!
        It should be computed once, then put into wn.constants.
        """
        depth = 0
        for ss in self.all_synsets(pos):
            try:
                depth = max(depth, ss.max_depth())
            except RuntimeError:
                _msg = '{} throws error when searching for max_depth'.format(ss)
                raise WordNetError(_msg)
        if simulate_root:
            depth += 1
        return depth

    def get_version(self):
        filename = wordnet_dir+'/data.adj'
        with open(filename) as fin:
            for line in fin:
                match = re.search(r'WordNet (\d+\.\d+) Copyright', line)
                if match:
                    self._version = match.group(1)
                    return self._version
        raise WordNetError("Cannot find version number in {}".format(filename))

    def version(self):
        if hasattr(self, '_version'):
            return self._version
        return self.get_version()

    def _compute_max_depth(self, pos, simulate_root):
        """
        Compute the max depth for the given part of speech.  This is
        used by the lch similarity metric.
        """
        pos = 'a' if pos == 's' else pos
        # Try to fetch wordnet's max_depth from constants.
        version = self.version()
        #if version in WN_MAX_DEPTH or hasattr(self, '_max_depth'):
        #    self._max_depth = WN_MAX_DEPTH
        #    return self._max_depth[version][simulate_root][pos]

        # Compute the _wn_max_depth for this wordnet version for the first time.
        self._max_depth = {version: {True: {}, False: {}}}
        for _pos in POS_LIST:
            if _pos == 's': # Skips the satellite adjective.
                continue
            depth = self._max_depth[version][False][_pos] = 0
            for ss in self.all_synsets(_pos):
                depth = max(depth, ss.max_depth())
            self._max_depth[version][True][_pos] = depth + 1
            self._max_depth[version][False][_pos] = depth
        return self._max_depth[version][simulate_root][pos]


wordnet = WordNet()
