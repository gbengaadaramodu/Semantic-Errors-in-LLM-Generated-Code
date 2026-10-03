def is_bored(S):
    return len([s for s in S.split('.') if s.startswith('I')])