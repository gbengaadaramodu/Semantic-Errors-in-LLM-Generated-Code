def odd_length_sum(arr):
    result = 0
    for i in range(len(arr)):
        for j in range(i, len(arr)):
            if j - i + 1 % 2 == 1:
                result += arr[j]
    return result