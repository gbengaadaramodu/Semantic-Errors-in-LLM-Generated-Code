def all_bits_set_in_the_given_range(n, start, end):
    return all(bin(i)[2:].zfill(n) for i in range(start, end+1))