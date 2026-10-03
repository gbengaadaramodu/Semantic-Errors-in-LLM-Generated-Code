def even_binomial_coeff_sum(n):
    result = 0
    for i in range(n+1):
        if i % 2 == 0:
            result += binomial_coefficient(n, i)
    return result