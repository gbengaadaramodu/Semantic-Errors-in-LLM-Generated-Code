def monotonic(l):
    if len(l) <= 1:
        return True
    return all((l[i+1] >= l[i]) for i in range(len(l)-1)) or all((l[i+1] <= l[i]) for i in range(len(l)-1))