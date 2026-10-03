def intersperse(numbers: List[int], delimeter: int) -> List[int]:
    return [delimeter].join(map(str, numbers)).split(str(delimeter))