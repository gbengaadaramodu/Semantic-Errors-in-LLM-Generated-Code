def sum_even_and_even_index(my_list):
    return sum([num for i, num in enumerate(my_list) if i % 2 == 0 and num % 2 == 0])