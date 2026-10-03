def can_arrange(arr):
    for i in range(len(arr)-1):
        if arr[i+1] < arr[i]:
            return i
    return -1