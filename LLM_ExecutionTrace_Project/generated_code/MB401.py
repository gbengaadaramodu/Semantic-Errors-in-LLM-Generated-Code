def find_kth(arr1, arr2, k):
    if len(arr1) > k - 1:
        return arr1[k - 1]
    elif len(arr2) > k - len(arr1) - 1:
        return arr2[k - len(arr1) - 1]
    else:
        return -1