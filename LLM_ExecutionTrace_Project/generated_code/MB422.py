def pack_consecutive_duplicates(my_list):
    sublists = []
    for i in range(len(my_list)):
        if i == 0 or my_list[i] != my_list[i-1]:
            sublists.append([my_list[i]])
        else:
            sublists[-1].append(my_list[i])
    return sublists