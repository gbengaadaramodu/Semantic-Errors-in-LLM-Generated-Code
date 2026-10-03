def pair_xor_sum(my_list, n):
    result = 0
    for i in range(n):
        for j in range(i+1, n):
            result += my_list[i] ^ my_list[j]
    return result