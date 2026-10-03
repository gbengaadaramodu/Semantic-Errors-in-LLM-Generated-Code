def amicable_numbers_sum(n):
    sum = 0
    for i in range(1, n+1):
        if is_amicable(i):
            sum += i
    return sum

def is_amicable(n):
    s = sum_proper_divisors(n)
    return s != n and s == sum_proper_divisors(s)

def sum_proper_divisors(n):
    sum = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            sum += i
            if n // i != i:
                sum += n // i
    return sum