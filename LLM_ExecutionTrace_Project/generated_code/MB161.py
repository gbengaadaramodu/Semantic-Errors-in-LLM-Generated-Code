def are_equivalent(num1, num2):
    return sum(divisors(num1)) == sum(divisors(num2))