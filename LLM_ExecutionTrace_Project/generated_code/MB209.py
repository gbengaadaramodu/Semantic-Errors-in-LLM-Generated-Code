def count_element_in_list(my_list, element):
    count = 0
    for sublist in my_list:
        if element in sublist:
            count += 1
    return count