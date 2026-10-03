def right_insertion(my_list, value):
    for i in range(len(my_list)):
        if my_list[i] > value:
            return i
    return len(my_list)