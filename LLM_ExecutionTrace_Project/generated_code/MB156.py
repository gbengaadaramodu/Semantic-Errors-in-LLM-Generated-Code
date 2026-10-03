def tuple_intersection(tuple_list1, tuple_list2):
    return {t for t in set(tuple_list1) & set(tuple_list2)}