def count_no_of_ways(n, k):
    if n == 0:
        return 0
    if n == 1:
        return k
    if k == 1:
        return 1
    return (k * count_no_of_ways(n-1, k-1)) + count_no_of_ways(n-1, k)