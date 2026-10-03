def make_palindrome(string: str) -> str:
    if is_palindrome(string):
        return string

    longest_postfix = ""
    for i in range(len(string), 0, -1):
        if is_palindrome(string[:i]):
            longest_postfix = string[i:]
            break

    return string + longest_postfix[::-1]