def expensive_items(data, n):
    return sorted(data, key=lambda x: x['price'], reverse=True)[:n]