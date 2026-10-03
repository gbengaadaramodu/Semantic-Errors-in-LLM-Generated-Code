def find_lists(my_tuple):
    return len([x for x in my_tuple if isinstance(x, list)])