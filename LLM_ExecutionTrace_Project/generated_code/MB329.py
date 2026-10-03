def sum_common_divisors(num1, num2):
    return sum(set(range(1, num1 + 1)).intersection(range(1, num2 + 1)))