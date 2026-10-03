def encrypt(s):
    # Create a new string to store the encrypted text
    encrypted_text = ""

    # Iterate through each character in the input string
    for char in s:
        # Rotate the character by two places
        rotated_char = chr((ord(char) - 97 + 2) % 26 + 97)

        # Add the rotated character to the encrypted text
        encrypted_text += rotated_char

    # Return the encrypted text
    return encrypted_text