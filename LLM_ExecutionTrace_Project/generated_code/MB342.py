def find_length(binary_string):
    count_zeros = 0
    count_ones = 0
    max_diff = 0
    for char in binary_string:
        if char == "0":
            count_zeros += 1
        else:
            count_ones += 1
        diff = abs(count_zeros - count_ones)
        if diff > max_diff:
            max_diff = diff
    return max_diff