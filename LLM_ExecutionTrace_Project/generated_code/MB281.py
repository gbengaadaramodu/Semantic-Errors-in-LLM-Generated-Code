def is_majority(sorted_array, n, element):
    if sorted_array[n//2] == element:
        return True
    if n % 2 == 0:
        return False
    if element > sorted_array[n//2]:
        return is_majority(sorted_array, n//2, element)
    else:
        return is_majority(sorted_array, n//2+1, element)