def change_base(x: int, base: int):
    if x == 0:
        return "0"
    digs = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    while x > 0:
        r = x % base
        x = x // base
        res = digs[r] + res
    return res