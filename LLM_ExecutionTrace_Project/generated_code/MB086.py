def largest_subset(my_list):
    my_list.sort()
    max_length = 0
    for i in range(len(my_list)):
        num = my_list[i]
        j = i + 1
        while j < len(my_list) and my_list[j] % num == 0:
            j += 1
        max_length = max(max_length, j - i)
    return max_length