def extract_values(string):
    return re.findall(r'"([^"]*)"', string)