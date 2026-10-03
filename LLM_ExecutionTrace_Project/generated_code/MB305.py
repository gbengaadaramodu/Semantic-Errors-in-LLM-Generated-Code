def two_unique_nums(my_lists):
    unique_nums = []
    for num in my_lists:
        if num not in unique_nums:
            unique_nums.append(num)
    return unique_nums