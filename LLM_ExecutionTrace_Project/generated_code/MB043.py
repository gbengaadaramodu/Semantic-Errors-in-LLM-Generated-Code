def lps(s):
    # Initialize a two-dimensional matrix with zeros
    dp = [[0 for x in range(len(s) + 1)] for y in range(len(s) + 1)]

    # Populate the first row and column with ones
    for i in range(1, len(s) + 1):
        dp[i][0] = 1
    for j in range(1, len(s) + 1):
        dp[0][j] = 1

    # Fill in the rest of the matrix
    for i in range(1, len(s) + 1):
        for j in range(1, len(s) + 1):
            if s[i - 1] == s[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # Return the longest palindromic subsequence length
    return dp[len(s)][len(s)]