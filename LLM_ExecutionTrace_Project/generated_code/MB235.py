def pancake_sort(my_list):
    for i in range(len(my_list)-1, 0, -1):
        max_index = 0
        for j in range(1, i+1):
            if my_list[j] > my_list[max_index]:
                max_index = j
        my_list[i], my_list[max_index] = my_list[max_index], my_list[i]
    return my_list