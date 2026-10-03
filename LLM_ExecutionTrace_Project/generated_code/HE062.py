def match_parens(lst):
    if len(lst) % 2 == 1:
        return "No"
    stack = []
    for i in range(len(lst)):
        if lst[i] == '(':
            stack.append(lst[i])
        else:
            if not stack:
                return "No"
            stack.pop()
    if not stack:
        return "Yes"
    return "No"