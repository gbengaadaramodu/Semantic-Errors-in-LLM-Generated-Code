def min_k(my_list, k):
    return sorted(my_list, key=lambda x: x[1])[:k]