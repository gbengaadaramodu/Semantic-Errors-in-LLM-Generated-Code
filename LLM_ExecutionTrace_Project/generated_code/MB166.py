def divisible_by_digits(startnum, endnum):
    return [num for num in range(startnum, endnum+1) if all(int(digit) for digit in str(num))]