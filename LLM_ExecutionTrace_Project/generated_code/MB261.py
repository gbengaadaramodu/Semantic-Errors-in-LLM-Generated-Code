def count_substrings(s):
    count = 0
    for i in range(len(s)):
        for j in range(i+1, len(s)+1):
            if sum(int(x) for x in s[i:j]) == j-i:
                count += 1
    return count