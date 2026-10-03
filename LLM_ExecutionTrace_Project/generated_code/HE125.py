def prod_signs(arr):
    if not arr:
        return None
    signs = [1 for _ in arr]
    for i, num in enumerate(arr):
        if num < 0:
            signs[i] *= -1
    return sum(map(abs, arr)) * prod(signs)