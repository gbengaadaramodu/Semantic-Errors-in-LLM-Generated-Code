def count_same_pair(list1, list2):
    return sum(1 for i in range(len(list1)) if list1[i] == list2[i])