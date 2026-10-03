def catalan_number(n):
    if n <= 1:
        return 1
    else:
        return sum(catalan_number(i) * catalan_number(n-i-1) for i in range(n))