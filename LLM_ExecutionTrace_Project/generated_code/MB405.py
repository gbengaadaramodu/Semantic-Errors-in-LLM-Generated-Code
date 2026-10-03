def count_char_position(input_string):
    count = 0
    for i, c in enumerate(input_string):
        if c.lower() == chr(i + ord('a')):
            count += 1
    return count