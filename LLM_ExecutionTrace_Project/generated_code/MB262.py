def get_lucid(n):
    lucid_numbers = []
    for i in range(1, n+1):
        if i == 1:
            lucid_numbers.append(i)
        else:
            flag = True
            for j in range(2, int(i**0.5)+1):
                if i % j == 0:
                    flag = False
                    break
            if flag:
                lucid_numbers.append(i)
    return lucid_numbers