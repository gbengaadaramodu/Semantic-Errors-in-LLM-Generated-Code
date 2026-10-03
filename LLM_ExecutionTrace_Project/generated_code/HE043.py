def sort_third(l):
    l_copy = l.copy()
    for i in range(len(l)):
        if i % 3 == 0:
            continue
        else:
            l_copy[i] = sorted(l_copy[i])
    return l_copy