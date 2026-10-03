def find_even_pair(my_list):
    count = 0
    for i in range(len(my_list)):
        for j in range(i+1, len(my_list)):
            if (my_list[i] ^ my_list[j]) % 2 == 0:
                count += 1
    return count