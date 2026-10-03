def rearrange_bigger(num):
    num_str = str(num)
    num_list = list(num_str)
    num_list.sort(reverse=True)
    return int(''.join(num_list))