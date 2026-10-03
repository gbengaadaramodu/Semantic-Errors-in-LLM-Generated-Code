def sumOfFactors(n):
    return sum([i for i in range(2, n+1, 2) if n % i == 0])