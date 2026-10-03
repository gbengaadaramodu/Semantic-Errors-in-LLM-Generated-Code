def find_element(arr, queries, index):
    for query in queries:
        arr = arr[query[0]:] + arr[:query[0]]
    return arr[index]