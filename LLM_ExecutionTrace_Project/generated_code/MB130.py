def first_repeated_char(string):
    for char in string:
        if string.count(char) > 1:
            return char
    return None