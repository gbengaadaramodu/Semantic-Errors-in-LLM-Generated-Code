def group_tuples(my_list):
    result = []
    for tup in my_list:
        if tup[0] in [tup[0] for tup in result]:
            result.append(tup)
        else:
            result.append([tup[0], tup[1]])
    return result