def move_num(my_str):
    return ''.join(ch for ch in my_str if not ch.isdigit()) + ''.join(ch for ch in my_str if ch.isdigit())