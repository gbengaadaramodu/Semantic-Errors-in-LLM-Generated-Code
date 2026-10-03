def count_vowels(input_string):
    vowels = ["a", "e", "i", "o", "u"]
    count = 0
    for i in range(len(input_string)):
        if input_string[i].lower() in vowels:
            if i > 0 and input_string[i-1].lower() in vowels:
                count += 1
            if i < len(input_string) - 1 and input_string[i+1].lower() in vowels:
                count += 1
    return count