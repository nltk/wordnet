
import re

from collections import defaultdict
from lazyme import find_files, per_chunk

from wn.lemma import Lemma
from wn.synset import Synset

def parse_wordnet_line(wordnet_line, parse_verb_frame=False):
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
        # If the lemma has a syntactic marker, extract it.
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
    synset = Synset(offset, pos, first_lemma_name, lexname_index, synset_name,
                    definition, examples, synset_pointers, lemmas_objects, wordnet_line)

    # Return the important stuff.
    return synset, lemmas_objects


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



































    #
