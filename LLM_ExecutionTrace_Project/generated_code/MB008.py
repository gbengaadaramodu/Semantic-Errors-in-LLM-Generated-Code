def count_first_elements(my_tuple):
    count = 0
    for i in range(len(my_tuple)):
        if my_tuple[i] == (4, 6):
            break
        count += 1
    return count