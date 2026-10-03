def count_nums(arr):
    return sum(1 for x in arr if x > 0 or (x < 0 and any(int(d) < 0 for d in str(x))))