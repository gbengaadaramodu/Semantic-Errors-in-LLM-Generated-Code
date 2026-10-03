def highest_power_of_2(n):
    if n <= 1:
        return n
    
    power = 1
    while power < n:
        power *= 2
        
    return power // 2