def by_length(arr):
    if not arr:
        return []
    nums = sorted([str(num) for num in arr])
    names = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    return [names[int(num)-1] for num in nums]