def validate(n):
    digits = list(str(n))
    for d in digits:
        if digits.count(d) > int(d):
            return False
    return True