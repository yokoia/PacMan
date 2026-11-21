from collections import deque
from src.maze import Maze


def bfs(
    maze: Maze,
    start: tuple[int, int],
    target: tuple[int, int]
) -> list[tuple[int, int]]:

    """
    Initialize a BFS search to find the shortest path from start to target.
    """
    queue = deque([start])
    visited = {start}
    parent: dict[tuple[int, int], tuple[int, int]] = {}

    while queue:
        current = queue.popleft()

        if current == target:
            path = [current]

            while current != start:
                current = parent[current]
                path.append(current)

            path.reverse()
            return path

        for neighbor in maze.get_neighbors(*current):
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    return []
