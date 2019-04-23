# -*- coding: utf-8 -*-

import io
import os
from collections import defaultdict

from wn.constants import omw_dir

def parse_omw_line(omw_line):
    offset_pos, lemma_type, lemma  = omw_line.strip().split('\t')
    offset, pos = offset_pos.split('-')
    return int(offset), pos, lemma_type, lemma

class OpenMultilingualWordNet:
    @staticmethod
    def custom_lemmas(lang):
        """
        Reads a custom tab file containing mappings of lemmas in the given
        language to Princeton WordNet 3.0 synset offsets, allowing NLTK's
        WordNet functions to then be used with that language.
        See the "Tab files" section at http://compling.hss.ntu.edu.sg/omw/ for
        documentation on the Multilingual WordNet tab file format.
        :param tab_file: Tab file as a file or file-like object
        :type  lang str
        :param lang ISO 639-3 code of the language of the tab file
        """
        if len(lang) != 3:
            raise WordNetError('lang should be a (3 character) ISO 639-3 code')
        offsets_to_lemmas = defaultdict(lambda: defaultdict(list))
        lemmas_to_offsets = defaultdict(lambda: defaultdict(list))
        try:
            with io.open(omw_dir+'/{lang}/wn-data-{lang}.tab'.format(lang=lang), encoding='utf8') as fin:
                next(fin) # Skip first line.
                for line in fin:
                    if line.startswith('#'): # Skip commented lines.
                        continue
                    offset, pos, lemma_type, lemma = parse_omw_line(line)
                    lemma = lemma.strip().replace(' ', '_')
                    offsets_to_lemmas[pos][offset].append(lemma)
                    lemmas_to_offsets[pos][lemma.lower()].append(offset)
        except FileNotFoundError:
            raise WordNetError("Language is not supported.")
        # Make sure no more entries are accidentally added subsequently.
        offsets_to_lemmas.default_factory = None
        lemmas_to_offsets.default_factory = None
        return offsets_to_lemmas, lemmas_to_offsets

    def ss2of(self, ss, lang=None):
        ''' return the ID of the synset '''
        pos = ss.pos()
        # Only these 3 WordNets retain the satellite pos tag
        if lang not in ["nld", "lit", "slk"] and pos == 's':
            pos = 'a'
        return "{:08d}-{}".format(ss.offset(), pos)

    def langs(self):
        ''' return a list of languages supported by Multilingual Wordnet '''
        if hasattr(self, '_langs'):
            return self._langs
        else:
            self._langs = ['eng']
            for name in os.listdir(omw_dir):
                if os.path.isdir(os.path.join(omw_dir, name)):
                    self._langs.append(name)
            return self._langs

    def _load_lang_data(self, lang):
        ''' load the wordnet data of the requested language from the file to
        the cache, _lang_data '''
        if lang in _lang_to_lemmas_to_offsets.keys():
            if lang in _lang_to_offsets_to_lemma.keys(): # Paranoid check.
                return
        if lang not in self.langs():
            raise WordNetError("Language is not supported.")
        # If not in cache, load the OMW.
        offsets_to_lemmas, lemmas_to_offsets = self.custom_lemmas(lang)
        _lang_to_offsets_to_lemma[lang] = offsets_to_lemmas
        _lang_to_lemmas_to_offsets[lang] = lemmas_to_offsets
