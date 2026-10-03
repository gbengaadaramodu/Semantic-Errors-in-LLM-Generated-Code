def max_sum_increasing_subseq(nums, i, k, prefix_sum):
    if i == k:
        return nums[i]
    if i > k:
        return 0
    if prefix_sum[k] != -1:
        return prefix_sum[k]
    max_sum = 0
    for j in range(i, k+1):
        max_sum = max(max_sum, nums[j] + max_sum_increasing_subseq(nums, j+1, k, prefix_sum))
    prefix_sum[k] = max_sum
    return max_sum