def max_subarray_product(arr):
    if len(arr) == 0:
        return None
    max_product = arr[0]
    min_product = arr[0]
    for i in range(1, len(arr)):
        product = arr[i] * max_product
        if product > max_product:
            max_product = product
        product = arr[i] * min_product
        if product < min_product:
            min_product = product
    return max_product