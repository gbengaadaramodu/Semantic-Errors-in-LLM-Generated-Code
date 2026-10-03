def add_pairwise(my_tuple):
    return tuple(sum(t) for t in zip(my_tuple, my_tuple[1:]))