def find_combinations(tuple_list):
    combinations = []
    for i in range(len(tuple_list)):
        for j in range(i+1, len(tuple_list)):
            combinations.append((tuple_list[i][0] + tuple_list[j][0], tuple_list[i][1] + tuple_list[j][1]))
    return combinations