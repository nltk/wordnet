
import re

from collections import defaultdict
from lazyme import find_files, per_chunk

def parse_wordnet_line(wordnet_line, parse_verb_frame=False):
    # Split the network information from the gloss.
    columns_str, gloss = wordnet_line.strip().split('|')
    # Extract the definition and examples from the gloss.
    definition = re.sub(r"[\"].*?[\"]", "", gloss)
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
    for symbol, offset, pos, lemma_ids_str in per_chunk(pointers_tokens, 4):
        if lemma_ids_str == '0000':
            synset_pointers[symbol].add((pos, offset))
        else:
            source_index = int(lemma_ids_str[:2], 16) - 1
            target_index = int(lemma_ids_str[2:], 16) - 1
            source_lemma_name = lemmas[source_index][0]
            lemma_pointers[source_lemma_name, symbol] = (pos, offset, target_index)

    # The next rest of the terms (i.e. `frame_count` * 3)
    # are verb frame information.
    if parse_verb_frame and the_rest[pointers_end:]:
        frame_count = the_rest[pointers_end]
        for plus, frame_number, lemma_number in per_chunk(the_rest[pointers_end+1:], 3):
            # TODO: need to write for verb frame.
            ##print(plus, frame_number, lemma_number)
            pass

    # Return the important stuff.
    return offset, lexname_index, pos, n_lemmas, lemmas, synset_pointers, lemma_pointers
