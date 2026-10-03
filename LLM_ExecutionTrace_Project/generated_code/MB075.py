def check_occurences(my_list):
    occurences = {}
    for tup in my_list:
        if tup in occurences:
            occurences[tup] += 1
        else:
            occurences[tup] = 1
    return occurences