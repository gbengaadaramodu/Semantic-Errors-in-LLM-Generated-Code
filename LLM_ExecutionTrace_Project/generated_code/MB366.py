def check_consecutive(my_list):
    return all(my_list[i+1] == my_list[i] + 1 for i in range(len(my_list)-1))