def text_starta_endb(string):
    return re.match(r"a.*b$", string) is not None