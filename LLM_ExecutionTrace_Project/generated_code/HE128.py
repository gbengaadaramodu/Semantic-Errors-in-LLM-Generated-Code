def find_zero(xs):
    if len(xs) % 2 == 0 and xs[-1] != 0:
        return -xs[-2]/xs[-1]
    else:
        return None