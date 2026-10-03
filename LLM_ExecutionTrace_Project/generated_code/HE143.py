def will_it_fly(q, w):
    return all(x <= w for x in q) and any(x == y for x, y in zip(q, reversed(q)))