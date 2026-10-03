def search(my_list):
    mid = len(my_list) // 2
    if mid == 0:
        return my_list[0]
    left_half = my_list[:mid]
    right_half = my_list[mid:]
    if left_half[-1] == right_half[0]:
        return search(left_half)
    else:
        return left_half[-1]