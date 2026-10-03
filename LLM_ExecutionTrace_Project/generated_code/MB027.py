def max_occurrences(my_list):
    if not my_list:
        return None
    return max(set(my_list), key=my_list.count)