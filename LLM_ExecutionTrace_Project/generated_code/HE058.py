def smallest_change(arr):
    # Check if array is already palindromic
    if arr == arr[::-1]:
        return 0

    # Find the middle index of the array
    mid = len(arr) // 2

    # Reverse the second half of the array
    arr[mid:] = arr[mid:][::-1]

    # Check if the array is now palindromic
    if arr == arr[::-1]:
        return 1

    # Find the minimum number of elements needed to be changed
    left, right = 0, len(arr) - 1
    count = 0
    while left < right:
        if arr[left] != arr[right]:
            count += 1
        left += 1
        right -= 1

    return count + 2