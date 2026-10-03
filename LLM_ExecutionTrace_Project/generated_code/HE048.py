def pluck(arr):
    even_values = [node for node in arr if node % 2 == 0]
    if not even_values:
        return []
    smallest_even_value = min(even_values)
    smallest_index = arr.index(smallest_even_value)
    return [smallest_even_value, smallest_index]