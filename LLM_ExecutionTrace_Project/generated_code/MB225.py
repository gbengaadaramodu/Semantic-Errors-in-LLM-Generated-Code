def max_sub_array_sum(arr, k):
    max_sum = 0
    for i in range(len(arr)):
        sum = 0
        for j in range(i, min(len(arr), i+k)):
            sum += arr[j]
            if sum > max_sum:
                max_sum = sum
    return max_sum