def separate_paren_groups(paren_string: str) -> List[str]:
    groups = []
    for group in paren_string.split(")"):
        if group != "":
            groups.append(group + ")")
    return groups