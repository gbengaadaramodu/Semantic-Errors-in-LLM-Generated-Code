def even_odd_count(num):
    even_digits = 0
    odd_digits = 0
    while num > 0:
        if num % 10 % 2 == 0:
            even_digits += 1
        else:
            odd_digits += 1
        num //= 10
    return even_digits, odd_digits