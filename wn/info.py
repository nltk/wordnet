
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
                    offset = 0
                if value != 0:
                    self.ic[pos][offset] = value
