def find_first_missing(my_list):
    for i in range(len(my_list)):
        if my_list[i] != i:
            return i
    return len(my_list)