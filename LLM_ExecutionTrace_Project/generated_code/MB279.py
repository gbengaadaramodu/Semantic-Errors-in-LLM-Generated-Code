def max_abs_diff(arr):
    return max([abs(arr[i] - arr[i-1]) for i in range(1, len(arr))])