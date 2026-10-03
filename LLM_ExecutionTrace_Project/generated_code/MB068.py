def get_coordinates(coordinate):
    x, y = coordinate
    return [[x-1, y-1], [x-1, y], [x-1, y+1],
            [x,   y-1],           [x,   y+1],
            [x+1, y-1], [x+1, y], [x+1, y+1]]