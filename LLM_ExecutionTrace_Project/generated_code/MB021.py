def min_jumps(point, length):
    x, y = point
    if x == length and y == 0:
        return 1
    elif x > length or y > 0:
        return -1
    else:
        return 1 + min_jumps((x+1, y), length)