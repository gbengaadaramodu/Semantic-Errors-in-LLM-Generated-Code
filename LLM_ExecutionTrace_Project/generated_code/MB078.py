def text_lowercase_underscore(input_string):
    return any(c.islower() for c in input_string) and "_" in input_string