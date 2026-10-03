def exchange(lst1, lst2):
    if all(i % 2 == 0 for i in lst1):
        return "YES"
    else:
        return "NO"