def prime_fib(n: int):
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return a