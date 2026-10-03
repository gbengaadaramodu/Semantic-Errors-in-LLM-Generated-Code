def find_dissimilar(tuple1, tuple2):
    return tuple(set(tuple1) ^ set(tuple2))