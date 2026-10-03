def sum_of_product(n):
    return sum(binomial(i, j) * binomial(i + 1, j) for i in range(n) for j in range(i + 1))