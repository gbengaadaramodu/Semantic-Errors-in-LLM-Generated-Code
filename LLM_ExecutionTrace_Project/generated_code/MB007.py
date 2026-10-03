def eulerian_num(n, m):
    if n == 0 and m == 0:
        return 1
    elif n > 0 and m == 0:
        return 0
    elif n == 0 and m > 0:
        return eulerian_num(n, m-1)
    else:
        return eulerian_num(n-1, m-1) + eulerian_num(n-1, m)