def find_sum(my_list):
    seen = set()
    sum = 0
    for elem in my_list:
        if elem not in seen:
            sum += elem
            seen.add(elem)
    return sum