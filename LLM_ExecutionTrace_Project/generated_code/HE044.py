def rounded_avg(n, m):
    if n > m:
        return -1
    
    total = 0
    for i in range(n, m+1):
        total += i
        
    avg = total / (m - n + 1)
    rounded = round(avg)
    binary = bin(rounded)[2:]
    
    return binary