def frequency_lists(my_list):
    result = {}
    for sublist in my_list:
        for element in sublist:
            if element not in result:
                result[element] = 1
            else:
                result[element] += 1
    return result