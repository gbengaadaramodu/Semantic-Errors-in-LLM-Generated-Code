def valid_date(date_string):
    date_string = date_string.strip()
    if not date_string or len(date_string) != 10:
        return False
    if date_string[2] != '-' or date_string[5] != '-':
        return False
    try:
        int(date_string[:2])
        int(date_string[3:5])
        int(date_string[6:10])
    except ValueError:
        return False
    if not (1 <= int(date_string[:2]) <= 12):
        return False
    if int(date_string[:2]) in [1, 3, 5, 7, 8, 10, 12]:
        if not (1 <= int(date_string[3:5]) <= 31):
            return False
    elif int(date_string[:2]) in [4, 6, 9, 11]:
        if not (1 <= int(date_string[3:5]) <= 30):
            return False
    else:
        if not (1 <= int(date_string[3:5]) <= 28):
            return False
    return True