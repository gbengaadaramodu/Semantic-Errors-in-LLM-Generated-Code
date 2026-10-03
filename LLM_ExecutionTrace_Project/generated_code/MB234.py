def drop_empty(my_dict):
    return {k: v for k, v in my_dict.items() if v}