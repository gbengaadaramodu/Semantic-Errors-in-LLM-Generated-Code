def is_subarray(arr1, arr2):
    return all(x in arr1 for x in arr2)