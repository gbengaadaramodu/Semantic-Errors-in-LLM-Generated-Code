def mul_even_odd(my_list):
    even_num = None
    odd_num = None
    for num in my_list:
        if num % 2 == 0:
            even_num = num
            break
    for num in my_list:
        if num % 2 != 0:
            odd_num = num
            break
    return even_num * odd_num