def bell_number(n):
    if n == 0:
        return 1
    else:
        return sum([bell_number(i) * bell_number(n-i-1) for i in range(n)])