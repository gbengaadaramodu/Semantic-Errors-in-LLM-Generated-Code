def check_str(string):
    return re.match('^[aeiouAEIOU].*', string) is not None