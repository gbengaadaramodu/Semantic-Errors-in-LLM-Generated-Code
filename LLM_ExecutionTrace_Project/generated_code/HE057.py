def fib4(n):
    if n == 0:
        return 0
    if n == 1:
        return 0
    if n == 2:
        return 2
    if n == 3:
        return 0
    return fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4)