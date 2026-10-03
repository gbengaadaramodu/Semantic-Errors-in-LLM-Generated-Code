def max_fill(grid, capacity):
    # Initialize variables
    total_units = 0
    num_lowerings = 0

    # Iterate through the grid
    for row in grid:
        # Check if the current row is full
        if sum(row) == capacity:
            # If it is, add its units to the total and move on to the next row
            total_units += capacity
        else:
            # If it's not full, calculate the number of lowerings needed for this row
            num_lowerings += capacity - sum(row)
            # Add the units in this row to the total
            total_units += sum(row)

    return num_lowerings