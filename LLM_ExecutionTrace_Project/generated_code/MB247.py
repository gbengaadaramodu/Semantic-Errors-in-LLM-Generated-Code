def max_product_tuple(tuples):
    max_product = 0
    for i in range(len(tuples)):
        for j in range(i+1, len(tuples)):
            product = abs(tuples[i][0] * tuples[j][1]) + abs(tuples[i][1] * tuples[j][0])
            if product > max_product:
                max_product = product
    return max_product