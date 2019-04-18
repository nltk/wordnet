
from collections import deque

from wn.utils import FakeSynset

def find_root_hypernyms(synset):
    """Get the topmost hypernyms of this synset in WordNet."""
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
