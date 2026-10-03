def reverse_delete(s, c):
    result = ''
    for char in s:
        if char not in c:
            result += char
    is_palindrome = result == result[::-1]
    return result, is_palindrome