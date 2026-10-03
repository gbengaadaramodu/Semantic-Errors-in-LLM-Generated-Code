def minPath(grid, k):
    rows = len(grid)
    cols = len(grid[0])
    visited = set()
    queue = [(0, 0, 1)]
    while queue:
        row, col, length = queue.pop(0)
        if (row, col) in visited:
            continue
        visited.add((row, col))
        if length == k:
            return grid[row][col]
        for r, c in [(row-1, col), (row+1, col), (row, col-1), (row, col+1)]:
            if 0 <= r < rows and 0 <= c < cols:
                queue.append((r, c, length+1))
    return []