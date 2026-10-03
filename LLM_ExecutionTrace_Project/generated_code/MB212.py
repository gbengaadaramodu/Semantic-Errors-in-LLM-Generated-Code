def magic_square_test(matrix):
    # Check if the matrix is a square matrix
    if len(matrix) != len(matrix[0]):
        return False

    # Check if the matrix is a magic square
    n = len(matrix)
    expected_sum = n * (n**2 + 1) // 2
    for row in matrix:
        if sum(row) != expected_sum:
            return False
    for col in zip(*matrix):
        if sum(col) != expected_sum:
            return False
    return True