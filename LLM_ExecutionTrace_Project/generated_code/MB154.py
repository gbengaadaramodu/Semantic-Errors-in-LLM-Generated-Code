def armstrong_number(n):
    original_num = n
    sum = 0
    while n > 0:
        digit = n % 10
        sum += digit ** 3
        n //= 10
    return original_num == sum