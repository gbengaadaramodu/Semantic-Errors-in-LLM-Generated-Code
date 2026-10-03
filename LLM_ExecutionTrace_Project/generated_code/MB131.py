def sequence(n):
    if n <= 2:
        return n
    else:
        return sequence(sequence(n-1)) + sequence(n-sequence(n-1))