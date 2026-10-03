def remove_nested(my_tuple):
    return tuple(x for x in my_tuple if not isinstance(x, tuple))