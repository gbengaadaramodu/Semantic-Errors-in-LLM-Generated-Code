def sum_Of_Subarray_Prod(arr):
    n = len(arr)
    dp = [[0 for _ in range(n+1)] for _ in range(n+1)]
    
    for i in range(n+1):
        dp[i][0] = 1
        
    for j in range(1, n+1):
        for i in range(j):
            dp[i][j] = dp[i][j-1] * arr[j-1]
    
    for i in range(n+1):
        for j in range(i+1, n+1):
            dp[i][j] += dp[i][j-1]
    
    return dp[0][n]