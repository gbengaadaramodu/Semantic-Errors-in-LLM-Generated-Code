def simplify(x, n):
    num1, denom1 = x.split('/')
    num2, denom2 = n.split('/')
    result = str(int(num1) * int(denom2)) + '/' + str(int(num2) * int(denom1))
    return result.endswith('/1')