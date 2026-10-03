def bitwise_xor(tup1, tup2):
    return tuple(i ^ j for i, j in zip(tup1, tup2))