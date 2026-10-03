def capital_words_spaces(string):
    return " ".join([word for word in string.split() if word[0].isupper()])