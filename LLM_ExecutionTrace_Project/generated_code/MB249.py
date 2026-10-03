def last(my_list, element):
    for i in range(len(my_list)-1, -1, -1):
        if my_list[i] == element:
            return i
    return -1