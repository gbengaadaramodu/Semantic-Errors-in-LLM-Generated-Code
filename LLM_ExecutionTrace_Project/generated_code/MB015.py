def newman_prime(n):
    if n < 1:
        return None
    if n == 1:
        return 2
    
    # find the previous prime number
    prev_prime = newman_prime(n-1)
    
    # find the next prime number after the previous prime
    next_prime = prev_prime + 2
    while not is_prime(next_prime):
        next_prime += 2
        
    return next_prime

def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True