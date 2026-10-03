def first_non_repeating_character(string):
    seen = set()
    for char in string:
        if char not in seen:
            seen.add(char)
        else:
            seen.remove(char)
    return seen.pop() if seen else None