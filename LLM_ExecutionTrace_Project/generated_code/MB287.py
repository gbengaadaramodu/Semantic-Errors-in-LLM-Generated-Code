def find_rotations(string):
    min_rotations = 1
    for i in range(len(string)):
        if string[i:] + string[:i] == string:
            min_rotations = i + 1
            break
    return min_rotations