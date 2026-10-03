def positive_count(arr):
    count = 0
    for num in arr:
        if num > 0:
            count += 1
    return count / len(arr)