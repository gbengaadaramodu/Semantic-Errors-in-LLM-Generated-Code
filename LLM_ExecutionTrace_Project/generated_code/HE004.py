def strange_sort_list(lst):
    if not lst:
        return []
    sorted_lst = sorted(lst)
    minimum = sorted_lst[0]
    maximum = sorted_lst[-1]
    return [minimum] + [maximum] + [x for x in sorted_lst if x != minimum and x != maximum]