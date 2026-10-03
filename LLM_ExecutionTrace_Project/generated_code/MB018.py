def find_solution(a, b, n):
    x = 0
    y = 0
    for i in range(n):
        if a*i + b*y == n:
            x = i
            break
    for j in range(n):
        if a*x + b*j == n:
            y = j
            break
    if x==0 and y==0:
        return None
    else:
        return (x,y)