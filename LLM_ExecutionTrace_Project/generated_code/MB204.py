def odd_equivalent(binary_string, num_rotations):
    # Initialize a counter for the number of odd values
    num_odd_values = 0

    # Loop through each rotation of the binary string
    for i in range(num_rotations):
        # Convert the binary string to an integer
        num = int(binary_string, 2)

        # Check if the integer is odd
        if num % 2 == 1:
            # Increment the counter for the number of odd values
            num_odd_values += 1

    # Return the number of odd values
    return num_odd_values