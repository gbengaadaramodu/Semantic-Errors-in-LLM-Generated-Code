def is_nested(string):
    stack = []
    for char in string:
        if char == "[" and len(stack) > 0 and stack[-1] == "]":
            return True
        elif char == "[":
            stack.append(char)
        elif char == "]" and len(stack) > 0 and stack[-1] == "[":
            stack.pop()
    return False