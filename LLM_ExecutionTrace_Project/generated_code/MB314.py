def max_sub_array_sum_repeated(arr, k, n):
    modified_array = []
    for i in range(k):
        modified_array += arr * n
    return max(modified_array)