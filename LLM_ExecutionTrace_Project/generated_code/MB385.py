def is_product_even(my_list):
    product = 1
    for num in my_list:
        product *= num
    return product % 2 == 0