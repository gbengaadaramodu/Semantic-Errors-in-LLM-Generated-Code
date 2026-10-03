def heap_sort(my_list):
    def heapify(arr, n, i):
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n and arr[i] < arr[l]:
            largest = l
        if r < n and arr[largest] < arr[r]:
            largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(arr, n, largest)
    if len(my_list) > 1:
        n = len(my_list)
        for i in range(n//2, -1, -1):
            heapify(my_list, n, i)
        for i in range(n-1, 0, -1):
            my_list[i], my_list[0] = my_list[0], my_list[i]
            heapify(my_list, i, 0)
    return my_list