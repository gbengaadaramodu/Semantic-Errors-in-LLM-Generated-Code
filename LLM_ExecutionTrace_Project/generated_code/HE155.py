def digitSum(s):
    upper_codes = sum([ord(c) for c in s if ord(c) >= 65 and ord(c) <= 90])
    return upper_codes