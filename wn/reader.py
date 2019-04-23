# -*- coding: utf-8 -*-

import re
import warnings
from collections import defaultdict

from wn.constants import lexnames
from wn.constants import _synset_types
from wn.lemma import Lemma
from wn.synset import Synset
from wn.utils import WordNetError
from wn.utils import per_chunk

def parse_wordnet_line(wordnet_line, parse_verb_frame=False, lexname_type=None):
    # Split the network information from the gloss.
    columns_str, gloss = wordnet_line.strip().split('|')
    # Extract the definition and examples from the gloss.
    definition = re.sub(r"[\"].*?[\"]", "", gloss).strip(';, ')
    examples = re.findall(r'"([^"]*)"', gloss)

    # The first 4 columns.
    offset, lexname_index, pos, n_lemmas, *the_rest = columns_str.split()
    offset = int(offset)
    lexname_index = int(lexname_index)
    n_lemmas = int(n_lemmas, 16)

    # The next `n_lemmas` * 2 terms are lemmas.
    lemma_tokens = the_rest[:n_lemmas*2]
    lemmas = []
    for lemma_name, lex_id in per_chunk(lemma_tokens, 2):
        lex_id = int(lex_id, 16)
        # If lemma matches any in the `_lemma_pos_offset_map`
        if lemma_name.lower() in _lemma_pos_offset_map:
            lemmas.append((lemma_name, lexname_index, lex_id, None))
        else: # Else, if the lemma has a syntactic marker, extract it.
            m = re.match(r'(.*?)(\(.*\))?$', lemma_name)
            lemma_name, syn_mark = m.groups()
            lemmas.append((lemma_name, lexname_index, lex_id, syn_mark))

    # Find the synset and lemma connections.
    synset_pointers = defaultdict(set)
    lemma_pointers = defaultdict(list)

    # The next `n_pointers` * 4 terms are edges connecting to the synset.
    n_pointers = int(the_rest[n_lemmas*2])
    pointers_start = n_lemmas*2+1
    pointers_end = pointers_start + n_pointers * 4
    pointers_tokens = the_rest[pointers_start:pointers_end]
    for symbol, pointer_offset, pointer_pos, lemma_ids_str in per_chunk(pointers_tokens, 4):
        if symbol.isdigit():
            print(symbol, pointer_offset, pointer_pos, lemma_ids_str)
        if lemma_ids_str == '0000':
            synset_pointers[symbol].add((pointer_pos, int(pointer_offset)))
        else:
            source_index = int(lemma_ids_str[:2], 16) - 1
            target_index = int(lemma_ids_str[2:], 16) - 1
            source_lemma_name = lemmas[source_index][0]
            lemma_pointers[source_lemma_name, symbol].append((pointer_pos, int(pointer_offset), int(target_index)))
            #print(offset, lemma_pointers)

    # The next rest of the terms (i.e. `frame_count` * 3)
    # are verb frame information.
    if parse_verb_frame and the_rest[pointers_end:]:
        frame_count = the_rest[pointers_end]
        for plus, frame_number, lemma_number in per_chunk(the_rest[pointers_end+1:], 3):
            # TODO: need to write for verb frame.
            ##print(plus, frame_number, lemma_number)
            pass


    # Copying behavior from NLTK
    # See https://github.com/nltk/nltk/blob/develop/nltk/corpus/reader/wordnet.py#L1512
    first_lemma_name = lemmas[0][0].lower()
    offsets = _lemma_pos_offset_map[first_lemma_name][pos]
    #print(offset, synset_name, pos, offsets)
    sense_index = offsets.index(offset)
    synset_name = "%s.%s.%02i" % (first_lemma_name, pos, sense_index+1)

    # First lemma name is the synset name.
    lemmas_objects = []
    # Creating the Lemma objects.
    for lemma in lemmas:
        ##lemma_name, lexname_index, lex_id, syn_mark = lemma
        lemmas_objects.append(Lemma(*lemma,
                                    synset_offset=offset,
                                    synset_pos=pos,
                                    synset_name=synset_name,
                                    lemma_pointers=lemma_pointers))
    # Create the Synset object
    _lexname = str(lexname_index) if lexname_type == 'clusters' else lexnames[lexname_index]
    synset = Synset(offset, pos, synset_name, lexname_index, _lexname,
                    definition, examples, synset_pointers, lemmas_objects, wordnet_line)

    # Return the important stuff.
    return synset, lemmas_objects


def fix_inconsistent_line(index_line):
    """ Fix inconsistent line in WordNet 3.3 """
    # Get the lemma and part-of-speech, no. of synsets and no. of pointers.
    lemma, pos, n_synsets, n_pointers, *the_rest = index_line.split()
    n_synsets, n_pointers = int(n_synsets), int(n_pointers)
    assert n_synsets > 0
    # Ignore the no. of pointers.
    # and ignore number of senses ranked according to frequency.
    pointers= the_rest[:-(n_synsets+2)]
    n_pointers = len(pointers)
    n_senses, not_used , *synset_offsets = the_rest[-(n_synsets+2):]
    n_senses = int(n_senses)
    assert n_senses == n_synsets, '{} {}'.format(n_senses, index_line)
    return ' '.join(map(str, [lemma, pos, n_synsets, n_pointers, ' '.join(pointers),
                     n_senses, not_used, ' '.join(synset_offsets)]))


def parse_index_line(index_line):
    # Get the lemma and part-of-speech, no. of synsets and no. of pointers.
    lemma, pos, n_synsets, n_pointers, *the_rest = index_line.split()
    n_synsets, n_pointers = int(n_synsets), int(n_pointers)
    assert n_synsets > 0
    # Ignore the no. of pointers.
    # and ignore number of senses ranked according to frequency.
    n_senses, _ , *synset_offsets = the_rest[n_pointers:]
    n_senses = int(n_senses)
    assert n_senses == n_synsets
    # Cast synset offets to integers
    synset_offsets = [int(so) for so in synset_offsets]
    return lemma, pos, synset_offsets


def parse_sense_key(sense_key):
    """
    Retrieves synset based on a given sense_key. Sense keys can be
    obtained from lemma.key()
    From https://wordnet.princeton.edu/wordnet/man/senseidx.5WN.html:
    A sense_key is represented as:
        lemma % lex_sense (e.g. 'dog%1:18:01::')
    where lex_sense is encoded as:
        ss_type:lex_filenum:lex_id:head_word:head_id

    lemma:      ASCII text of word/collocation, in lower case
    ss_type:    synset type for the sense (1 digit int)
                The synset type is encoded as follows:
                1    NOUN
                2    VERB
                3    ADJECTIVE
                4    ADVERB
                5    ADJECTIVE SATELLITE
    lex_filenum: name of lexicographer file containing the synset for the sense (2 digit int)
    lex_id:      when paired with lemma, uniquely identifies a sense in the lexicographer file (2 digit int)
    head_word:   lemma of the first word in satellite's head synset
                 Only used if sense is in an adjective satellite synset
    head_id:     uniquely identifies sense in a lexicographer file when paired with head_word
                 Only used if head_word is present (2 digit int)
    """
    sense_key_regex = re.compile(r"(.*)\%(.*):(.*):(.*):(.*):(.*)")
    lemma, ss_type, _, lex_id, _, _ = sense_key_regex.match(sense_key).groups()
    # check that information extracted from sense_key is valid
    error = None
    if not lemma:
        error = "lemma"
    elif int(ss_type) not in _synset_types:
        error = "ss_type"
    elif int(lex_id) < 0 or int(lex_id) > 99:
        error = "lex_id"
    if error:
        raise WordNetError(
            "valid {} could not be extracted from the sense key".format(error)
            )
    pos = _synset_types[int(ss_type)]
    return lemma, pos, lex_id


def parse_lemma_pos_index(lemma_pos_index):
    lemma, pos, synset_index_str = lemma_pos_index.lower().rsplit('.', 2)
    synset_index = int(synset_index_str) - 1
    # Get the offset for this synset
    try:
        offset = _lemma_pos_offset_map[lemma][pos][synset_index]
    except KeyError:
        message = 'no lemma %r with part of speech %r'
        raise WordNetError(message % (lemma, pos))
    except IndexError:
        n_senses = len(_lemma_pos_offset_map[lemma][pos])
        message = "lemma %r with part of speech %r has only %i %s"
        message = message % lemma, pos, n_senses, "sense"
        raise WordNetError(message if n_senses > 1 else message+'s')

    # If it's a confusion between adjective and satellite adjective,
    # users really doesn't care, so we resolve it and raise warning.
    if pos in ['a', 's']:
        # Raise error if user wants an `s` but offset is in `a`,
        if pos == 's' and offset in _synset_offset_cache['a']:
            message = (
                'adjective satellite requested but '
                'only plain adjective found for lemma %r'
                )
            raise WordNetError(message % lemma)
        # Push warning and change the POS
        # if user wants an `a` but offset is in `s`,
        elif pos == 'a' and offset in _synset_offset_cache['s']:
            message = (
                'plain adjective requested but '
                'only adjective satellite found for lemma %r'
                )
            warnings.warn(message % lemma)
            pos = 's' # Edit user specified POS.
    return pos, offset


def parse_wordnet_ic_line(ic_line):
    offset, value, *has_root = ic_line.strip().split()
    pos, has_root = offset[-1], bool(has_root)
    offset, value = int(offset[:-1]), float(value)
    if pos not in ['n', 'v']:
        raise WordNetError("Unidentified part of speech in "
                           "WordNet Information Content "
                           "file for field {}".format(line))
    return offset, value, pos, has_root
