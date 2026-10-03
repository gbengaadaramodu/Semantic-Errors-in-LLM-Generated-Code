def check_smaller(tuple1, tuple2):
    return all(t1 <= t2 for t1, t2 in zip(tuple1, tuple2))