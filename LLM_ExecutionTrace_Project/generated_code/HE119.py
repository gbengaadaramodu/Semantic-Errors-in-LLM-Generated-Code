def circular_shift(x, shift):
    if shift > len(str(x)):
        return str(x)[::-1]
    return str(x)[shift:] + str(x)[:shift]