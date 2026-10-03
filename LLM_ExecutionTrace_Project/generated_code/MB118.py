def multiply_elements(my_tuple):
    return tuple(x * y for x, y in zip(my_tuple, my_tuple[1:]))