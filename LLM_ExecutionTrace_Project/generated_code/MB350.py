def index_multiplication(tuple1, tuple2):
    return tuple((tup1 * tup2 for tup1, tup2 in zip(tuple1, tuple2)))