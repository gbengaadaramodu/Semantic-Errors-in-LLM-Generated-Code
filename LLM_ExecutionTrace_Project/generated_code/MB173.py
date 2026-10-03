def multiply_num(my_list):
    result = 1
    for num in my_list:
        result *= num
    return result / len(my_list)