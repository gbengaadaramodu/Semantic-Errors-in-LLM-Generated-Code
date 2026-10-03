def tuple_to_dict(my_tuple):
    return {my_tuple[i]: my_tuple[i+1] for i in range(len(my_tuple)-1)}