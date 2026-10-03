def fizz_buzz(n):
    count = 0
    for i in range(n):
        if i % 11 == 0 or i % 13 == 0:
            count += 1
    return count