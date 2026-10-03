def colon_tuple(my_tuple, start, end):
    return my_tuple[:start] + (end,) + my_tuple[start+1:]