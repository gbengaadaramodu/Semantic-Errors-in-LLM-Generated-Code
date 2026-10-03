def sort_even(l):
    return [l[i] for i in range(len(l)) if i % 2 == 0] + sorted([l[i] for i in range(len(l)) if i % 2 == 1])