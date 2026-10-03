def perfect_squares(start, end):
    return [x**2 for x in range(start, int(end**0.5) + 1)]