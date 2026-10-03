def sum_names(names):
    return sum(len(name) for name in names if name[0].isupper())