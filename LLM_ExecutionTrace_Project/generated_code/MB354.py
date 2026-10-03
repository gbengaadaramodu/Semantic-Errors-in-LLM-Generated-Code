def check_type(my_tuple):
    return all(isinstance(item, type(my_tuple[0])) for item in my_tuple)