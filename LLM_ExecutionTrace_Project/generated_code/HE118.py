def get_closest_vowel(word):
    vowels = "aeiou"
    for i in range(len(word)-1, -1, -1):
        if word[i] in vowels:
            return word[i]
    return ""