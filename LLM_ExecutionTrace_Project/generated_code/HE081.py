def prime_length(string):
    if len(string) == 1:
        return True
    for i in range(2, int(len(string) ** 0.5) + 1):
        if len(string) % i == 0:
            return False
    return True