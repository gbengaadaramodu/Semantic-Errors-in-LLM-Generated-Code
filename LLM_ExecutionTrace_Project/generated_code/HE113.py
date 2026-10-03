def search(lst):
    max_freq = max(lst)
    freq = lst.count(max_freq)
    if freq > max_freq:
        return max_freq
    else:
        return -1