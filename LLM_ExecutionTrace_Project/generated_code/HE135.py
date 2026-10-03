def eat(number, need, remaining):
    return [number + need, max(remaining - need, 0)]