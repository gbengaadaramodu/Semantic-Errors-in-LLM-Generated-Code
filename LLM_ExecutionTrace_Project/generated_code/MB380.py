def find_odd_pair(arr, k):
    return sum(1 for i in range(len(arr)) for j in range(i+1, len(arr)) if (arr[i] ^ arr[j]) % k == 0)