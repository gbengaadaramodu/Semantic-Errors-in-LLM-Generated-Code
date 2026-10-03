def find_min_diff(arr, n):
    arr.sort()
    min_diff = float("inf")
    for i in range(n-1):
        diff = arr[i+1] - arr[i]
        if diff < min_diff:
            min_diff = diff
    return min_diff