def max_sum(arr):
    # Find the maximum sum of a bitonic subsequence by dynamic programming
    
    # Initialize the maximum sum and its indices
    max_sum = 0
    start, end = 0, 0
    
    # Loop through the array and find the maximum sum
    for i in range(len(arr)):
        for j in range(i+1, len(arr)):
            if arr[i] + arr[j] > max_sum:
                max_sum = arr[i] + arr[j]
                start, end = i, j
    
    # Return the maximum sum and its indices
    return (max_sum, start, end)