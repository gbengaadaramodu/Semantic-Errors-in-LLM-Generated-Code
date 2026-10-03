def babylonian_squareroot(n):
    x = n
    while not math.isclose(x**2, n, rel_tol=0.001):
        x = (x + n/x) / 2
    return x