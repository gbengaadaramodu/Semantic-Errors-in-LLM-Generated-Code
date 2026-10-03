def parse_nested_parens(paren_string: str) -> List[int]:
    nesting_levels = []
    for group in paren_string.split():
        nesting_level = 0
        for char in group:
            if char == '(':
                nesting_level += 1
            elif char == ')':
                nesting_level -= 1
        nesting_levels.append(nesting_level)
    return nesting_levels