def find_remainder(arr, n):
    result = 1
    for i in arr:
        result = (result * i) % n
    return result