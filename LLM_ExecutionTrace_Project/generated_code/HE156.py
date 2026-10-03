def compare_one(a, b):
    if type(a) is not type(b):
        raise ValueError("a and b must be the same type")

    if a == b:
        return None
    elif a > b:
        return a
    else:
        return b