def extract_even(nested_tuple):
    result = []
    for item in nested_tuple:
        if isinstance(item, tuple):
            result.append(extract_even(item))
        elif item % 2 == 0:
            result.append(item)
    return tuple(result)