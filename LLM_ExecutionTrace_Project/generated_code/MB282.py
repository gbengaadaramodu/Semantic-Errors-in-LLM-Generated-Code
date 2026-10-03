def k_smallest_pairs(arr1, arr2, k):
    result = []
    for i in range(k):
        result.append([arr1[i], arr2[i]])
    return result