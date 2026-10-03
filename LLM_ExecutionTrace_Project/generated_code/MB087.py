def dif_square(n):
    for i in range(1, int(n**0.5)):
        if n % i == 0:
            return True
    return False