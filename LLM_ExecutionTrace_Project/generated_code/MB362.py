def odd_values_string(input_string):
    return "".join([char for i, char in enumerate(input_string) if i % 2 == 0])