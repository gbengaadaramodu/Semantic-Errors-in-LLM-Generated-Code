def digits(n):
    product = 1
    for digit in str(n):
        if digit.isdigit() and int(digit) % 2 != 0:
            product *= int(digit)
    return product