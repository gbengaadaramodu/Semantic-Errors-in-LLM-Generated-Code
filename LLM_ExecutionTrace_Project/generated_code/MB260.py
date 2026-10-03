def get_equal(tuples):
    return all(len(t) == len(tuples[0]) for t in tuples)