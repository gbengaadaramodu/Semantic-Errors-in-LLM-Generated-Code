def remove_dirty_chars(str1, str2):
    return ''.join([c for c in str1 if c not in str2])