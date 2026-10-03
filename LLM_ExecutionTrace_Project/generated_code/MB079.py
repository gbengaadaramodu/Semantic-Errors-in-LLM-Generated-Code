def min_swaps(n1, n2):
    count = 0
    for i in range(len(n1)):
        if n1[i] != n2[i]:
            count += 1
    return count