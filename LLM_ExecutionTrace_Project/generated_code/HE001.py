def generate_integers(a, b):
    return sorted([i for i in range(a, b+1) if str(i).isdigit() and int(str(i)) % 2 == 0])