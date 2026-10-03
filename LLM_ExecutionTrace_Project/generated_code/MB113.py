def loss_amount(sale_amount, loss_threshold):
    if sale_amount < loss_threshold:
        return 0
    else:
        return sale_amount - loss_threshold