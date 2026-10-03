def first_odd(my_list):
    for num in my_list:
        if num % 2 != 0:
            return num
    return None