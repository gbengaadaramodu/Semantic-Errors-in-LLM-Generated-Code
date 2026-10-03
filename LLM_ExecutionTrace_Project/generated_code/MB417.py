def add_nested_tuples(tuple1, tuple2):
    return tuple((i + j for i, j in zip(*tuple1)), (*tuple2))