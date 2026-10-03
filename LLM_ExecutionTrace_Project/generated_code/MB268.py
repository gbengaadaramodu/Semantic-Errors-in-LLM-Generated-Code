def get_char(s):
    return chr((ord(s[0]) + ord(s[1]) + ord(s[2])) % 26)