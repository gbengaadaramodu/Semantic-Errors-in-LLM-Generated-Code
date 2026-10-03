def comb_sort(my_list):
    gap = len(my_list)
    swapped = True
    while gap > 1 or swapped:
        gap = int(gap * 10 / 13)
        swapped = False
        for i in range(len(my_list) - gap):
            if my_list[i] > my_list[i + gap]:
                my_list[i], my_list[i + gap] = my_list[i + gap], my_list[i]
                swapped = True
    return my_list