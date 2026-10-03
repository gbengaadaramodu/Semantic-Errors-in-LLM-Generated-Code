def divisible_by_digits(start_num, end_num):
    return [num for num in range(start_num, end_num+1) if all(int(digit) for digit in str(num))]