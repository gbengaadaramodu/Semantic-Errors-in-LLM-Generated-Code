def next_smallest_palindrome(n):
    str_n = str(n)
    if str_n == str_n[::-1]:
        return n
    else:
        next_palindrome = int(str_n[::-1])
        if next_palindrome <= n:
            return next_palindrome
        else:
            return next_palindrome - 1