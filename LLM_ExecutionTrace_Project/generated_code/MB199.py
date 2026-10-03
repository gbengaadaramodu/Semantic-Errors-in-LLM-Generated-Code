def geometric_sum(n):
    if n == 0:
        return 0
    else:
        return (1 / n) + geometric_sum(n-1)