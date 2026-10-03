def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    numbers.sort()
    closest_pair = (numbers[0], numbers[1])
    diff = abs(closest_pair[0] - closest_pair[1])

    for i in range(2, len(numbers)):
        current_diff = abs(numbers[i] - numbers[i-1])
        if current_diff < diff:
            diff = current_diff
            closest_pair = (numbers[i-1], numbers[i])

    return closest_pair