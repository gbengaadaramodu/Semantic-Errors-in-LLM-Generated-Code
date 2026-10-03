def words_in_sentence(sentence):
    words = sentence.split()
    prime_word_indices = []
    for i, word in enumerate(words):
        if is_prime(len(word)):
            prime_word_indices.append(i)
    return " ".join([words[i] for i in prime_word_indices])

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True