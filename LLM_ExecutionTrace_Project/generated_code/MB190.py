def heap_queue_largest(numbers, n):
    return sorted(numbers, reverse=True)[:n]