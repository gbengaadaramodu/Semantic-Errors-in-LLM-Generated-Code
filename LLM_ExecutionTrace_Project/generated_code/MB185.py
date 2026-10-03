def check_value(my_dict, value):
    return all(x == value for x in my_dict.values())