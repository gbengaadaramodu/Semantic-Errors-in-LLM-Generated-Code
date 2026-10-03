def count_reverse_pairs(my_list):
    count = 0
    for i in range(len(my_list)):
        for j in range(i+1, len(my_list)):
            if my_list[i][::-1] == my_list[j]:
                count += 1
    return count