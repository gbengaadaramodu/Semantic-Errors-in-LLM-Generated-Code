def recursive_list_sum(my_list):
    total = 0
    for element in my_list:
        if isinstance(element, list):
            total += recursive_list_sum(element)
        else:
            total += element
    return total