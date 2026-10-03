def count_occurrence(my_tuple, my_list):
    count = 0
    for i in my_list:
        if i in my_tuple:
            count += 1
    return count