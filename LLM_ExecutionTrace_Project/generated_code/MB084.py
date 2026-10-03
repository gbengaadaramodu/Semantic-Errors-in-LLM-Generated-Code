def differ_at_one_bit_pos(num1, num2):
    return bin(num1 ^ num2).count('1') == 1