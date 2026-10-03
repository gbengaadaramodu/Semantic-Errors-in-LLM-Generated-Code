def text_match_two_three(string):
    return re.search(r"a(b{2,3})", string) is not None