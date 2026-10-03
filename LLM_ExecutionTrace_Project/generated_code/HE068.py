def make_a_pile(n):
    levels = []
    for i in range(n):
        if i % 2 == 0:
            levels.append(i + 1)
        else:
            levels.append(i + 2)
    return levels