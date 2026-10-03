def large_product(list1, list2, n):
    products = []
    for i in range(n):
        max_product = 0
        for j in range(len(list1)):
            product = list1[j] * list2[i]
            if product > max_product:
                max_product = product
        products.append(max_product)
    return products