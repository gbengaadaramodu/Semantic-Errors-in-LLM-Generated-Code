def count_rotation(arr):
    count = 0
    for i in range(len(arr)):
        if arr[i] != i+1:
            count += 1
    return count