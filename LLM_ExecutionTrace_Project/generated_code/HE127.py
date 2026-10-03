def is_multiply_prime(a):
    if a < 100:
        for i in range(2, int(a**0.5) + 1):
            if a % i == 0:
                return False
        return True
    else:
        return False