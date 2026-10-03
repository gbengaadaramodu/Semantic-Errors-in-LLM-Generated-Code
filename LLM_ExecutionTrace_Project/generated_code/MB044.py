def find_adverbs(text):
    adverbs = []
    for match in re.finditer(r'\b\w+ly\b', text):
        start, end = match.span()
        adverbs.append(f'{start}-{end}: {match.group()}')
    return ', '.join(adverbs)