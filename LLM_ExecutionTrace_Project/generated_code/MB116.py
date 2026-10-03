def is_samepatterns(patterns, sequence):
    return all(sequence[i] == patterns[i%len(patterns)] for i in range(len(sequence)))