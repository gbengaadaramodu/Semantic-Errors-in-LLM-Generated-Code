def max_Product(arr):
    if len(arr) == 0:
        return None
    max_product = arr[0]
    for i in range(1, len(arr)):
        if arr[i] > max_product:
            max_product = arr[i]
    return max_product