def even_position(my_list):
    return all(my_list[i] % 2 == 0 for i in range(len(my_list)) if i % 2 == 0)