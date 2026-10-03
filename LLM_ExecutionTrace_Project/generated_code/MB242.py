def check_expression(expression):
    stack = []
    for char in expression:
        if char == "(" or char == "[" or char == "{":
            stack.append(char)
        elif char == ")" or char == "]" or char == "}":
            if len(stack) == 0:
                return False
            top = stack.pop()
            if (top, char) not in [("(", ")"), ("[", "]"), ("{", "}")]:
                return False
    if len(stack) != 0:
        return False
    return True