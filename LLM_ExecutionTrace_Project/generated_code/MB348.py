def tuple_to_int(my_tuple):
    result = 0
    for num in my_tuple:
        result = result * 10 + num
    return result