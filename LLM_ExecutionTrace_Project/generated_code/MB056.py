def is_sum_of_powers_of_two(n):
    while n > 0:
        if n == 1:
            return True
        elif n % 2 != 0:
            return False
        n //= 2
    return False