def issort_list(my_list):
    return all(my_list[i] <= my_list[i+1] for i in range(len(my_list)-1))