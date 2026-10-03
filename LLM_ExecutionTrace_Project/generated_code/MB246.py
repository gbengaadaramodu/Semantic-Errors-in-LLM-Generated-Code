def is_decimal(s):
    return s.count('.') == 1 and all(c in '0123456789.' for c in s) and len(s.split('.')[1]) <= 2