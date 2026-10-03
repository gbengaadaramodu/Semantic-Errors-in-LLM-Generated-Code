def extract_singly(my_list):
    result = []
    for sublist in my_list:
        result.extend(sublist)
    return set(result)