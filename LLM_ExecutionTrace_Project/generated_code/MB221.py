def extract_quotation(my_string):
    import re
    return re.findall(r'"([^"]*)"', my_string)