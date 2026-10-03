def left_insertion(sorted_list, value):
    low = 0
    high = len(sorted_list) - 1
    while low <= high:
        mid = (low + high) // 2
        if sorted_list[mid] < value:
            low = mid + 1
        else:
            high = mid - 1
    return low