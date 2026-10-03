def tribonacci(n):
    if n == 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    t = [0, 1, 1]
    for i in range(n-3):
        t.append(t[0] + t[1] + t[2])
        t.pop(0)
    
    return t