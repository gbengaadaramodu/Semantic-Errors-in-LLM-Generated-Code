def check_dict_case(my_dict):
    if not my_dict:
        return False
    lowercase_keys = all(key.islower() for key in my_dict.keys())
    uppercase_keys = all(key.isupper() for key in my_dict.keys())
    return lowercase_keys or uppercase_keys