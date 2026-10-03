def zero_count(my_list):
    count = 0
    for num in my_list:
        if num == 0:
            count += 1
    return count