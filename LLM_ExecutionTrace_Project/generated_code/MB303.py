def sector_area(radius, angle):
    if angle > 360:
        return None
    else:
        return (angle / 360) * (2 * math.pi * radius**2)