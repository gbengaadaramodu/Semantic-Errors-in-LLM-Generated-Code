def cycpattern_check(a, b):
    return any(b in a for _ in range(len(a) - len(b) + 1))