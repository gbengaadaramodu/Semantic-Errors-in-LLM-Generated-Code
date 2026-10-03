def find_tuples(tuples, k):
    return [tuple for tuple in tuples if all(num % k == 0 for num in tuple)]