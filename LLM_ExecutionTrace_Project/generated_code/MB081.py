def get_total_number_of_sequences(m, n):
    if n == 1:
        return m
    if n == 2:
        return (m * (m - 1)) // 2
    if n == 3:
        return (m * (m - 1) * (m - 2)) // 6
    if n == 4:
        return (m * (m - 1) * (m - 2) * (m - 3)) // 24
    return 0