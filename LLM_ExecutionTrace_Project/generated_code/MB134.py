import re

def find_literals(string, pattern):
    regex = re.compile(pattern)
    match = regex.search(string)
    if match:
        return (match.group(), match.start(), match.end())
    else:
        return (None, None, None)