def long_words(n, words):
    return [word for word in words.split() if len(word) > n]