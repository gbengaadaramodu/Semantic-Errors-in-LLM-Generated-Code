def freq_count(my_list):
    return {item: my_list.count(item) for item in set(my_list)}