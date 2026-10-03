def replace_list(list1, list2):
    if not list1 or not list2:
        return []
    return list1[:-1] + list2