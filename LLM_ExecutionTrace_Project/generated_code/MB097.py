def re_arrange_array(arr, n):
    negative_elements = []
    positive_elements = []
    for i in range(n):
        if arr[i] < 0:
            negative_elements.append(arr[i])
        else:
            positive_elements.append(arr[i])
    return negative_elements + positive_elements