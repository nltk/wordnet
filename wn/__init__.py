
import os
from collections import defaultdict

from tqdm import tqdm
from lazyme import find_files

from wn.constants import *
from wn.constants import wordnet_dir
from wn.reader import parse_wordnet_line, parse_index_line

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
                        print(line)
                        raise

wordnet = WordNet()
