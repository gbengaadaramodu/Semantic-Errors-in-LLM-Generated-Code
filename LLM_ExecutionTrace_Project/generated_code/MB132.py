def count_bidirectional(tuple_pairs):
    return len(set((frozenset(pair), frozenset(reversed(pair))) for pair in tuple_pairs))