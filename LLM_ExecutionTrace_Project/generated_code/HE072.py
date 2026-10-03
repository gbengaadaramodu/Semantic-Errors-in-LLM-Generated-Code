def select_words(s, n):
    words = s.split()
    return [word for word in words if len(set(word).difference(set("aeiou"))) == n]