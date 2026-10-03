def find_substring(string_list, substring):
    for string in string_list:
        if substring in string:
            return True
    return False