def encode(message):
    encoded_msg = ''
    for char in message:
        if char.isalpha():
            if char.islower():
                encoded_msg += chr(ord('a') + (ord(char) - ord('a') + 2) % 26)
            else:
                encoded_msg += chr(ord('A') + (ord(char) - ord('A') + 2) % 26)
        else:
            encoded_msg += char
    return encoded_msg