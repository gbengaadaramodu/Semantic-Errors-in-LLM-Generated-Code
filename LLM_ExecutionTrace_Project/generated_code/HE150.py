def intersection(interval1, interval2):
    start1, end1 = interval1
    start2, end2 = interval2
    if start1 <= end1 and start2 <= end2:
        if start1 <= start2 <= end1:
            return "YES"
        elif start2 <= start1 <= end2:
            return "YES"
        else:
            return "NO"
    else:
        return "NO"