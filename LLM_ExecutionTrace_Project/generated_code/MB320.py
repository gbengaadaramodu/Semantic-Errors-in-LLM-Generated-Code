def left_rotate(n, d):
    return (n << d) | (n >> (32 - d))