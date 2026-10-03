def unique_product(my_list):
    return reduce(lambda x, y: x * y, set(my_list))