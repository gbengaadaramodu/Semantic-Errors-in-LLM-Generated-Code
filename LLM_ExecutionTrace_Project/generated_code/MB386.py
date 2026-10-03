def diff_even_odd(my_list):
    first_even = None
    first_odd = None
    for num in my_list:
        if num % 2 == 0 and first_even is None:
            first_even = num
        elif num % 2 == 1 and first_odd is None:
            first_odd = num
        if first_even is not None and first_odd is not None:
            break
    return abs(first_even - first_odd)