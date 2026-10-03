def double_the_difference(lst):
    result = 0
    for num in lst:
        if num < 0 or not num.is_integer():
            continue
        result += (num * num)
    return result