from src.maze import Maze, NORTH, SOUTH, EAST, WEST


class Entity:
    """
    Represents an entity in the game, such as Pac-Man or a ghost.
    """

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

        self.spawn_x = x
        self.spawn_y = y

    def can_move(self, direction: int, maze: Maze) -> bool:
        """
        Check if the entity can move in the specified direction.
        """
        if direction not in (NORTH, SOUTH, EAST, WEST):
            return False

        if maze.has_wall(self.x, self.y, direction):
            return False

        offsets = {
            NORTH: (0, -1),
            SOUTH: (0, 1),
            EAST: (1, 0),
            WEST: (-1, 0),
        }

        dx, dy = offsets[direction]

        new_x = self.x + dx
        new_y = self.y + dy

        if not (
            0 <= new_x < len(maze.grid[0])
            and 0 <= new_y < len(maze.grid)
        ):
            return False

        return True

    def move(self, direction: int, maze: Maze) -> bool:
        """
        Move the entity in the specified direction.
        """
        if not self.can_move(direction, maze):
            return False

        offsets = {
            NORTH: (0, -1),
            SOUTH: (0, 1),
            EAST: (1, 0),
            WEST: (-1, 0),
        }

        dx, dy = offsets[direction]

        self.x += dx
        self.y += dy
        return True

    def reset_position(self) -> None:
        """
        Reset the entity's position to its spawn point.
        """
        self.x = self.spawn_x
        self.y = self.spawn_y
