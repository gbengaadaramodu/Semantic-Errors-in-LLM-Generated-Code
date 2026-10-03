def largest_triangle_in_semi_circle(radius):
    if radius < 0:
        return None
    area = (math.sqrt(3)/2) * radius ** 2
    return area