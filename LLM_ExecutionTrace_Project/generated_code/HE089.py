def largest_prime(lst):
    prime_numbers = []
    for num in lst:
        if is_prime(num):
            prime_numbers.append(num)
    max_prime = max(prime_numbers)
    return sum_digits(max_prime)

def is_prime(n):
    if n == 1 or n == 0:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def sum_digits(n):
    total = 0
    while n > 0:
        total += n % 10
        n //= 10
    return total