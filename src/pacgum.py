from src.maze import Maze


class PacgumManager:
    """Manage Pacgums inside the Maze."""

    def __init__(self) -> None:
        self.pacgums: set[tuple[int, int]] = set()
        self.super_pacgums: set[tuple[int, int]] = set()

    def add_pacgum(self, x: int, y: int) -> None:
        """Add a pacgum at a given position"""
        self.pacgums.add((x, y))

    def eat_pacgum(self, x: int, y: int) -> bool:
        """Remove a Pacgum if it exists at the position."""
        position = (x, y)

        if position in self.pacgums:
            self.pacgums.remove(position)
            return True

        return False

    def generate_pacgums(
            self,
            maze: Maze,
            pacman_x: int,
            pacman_y: int
            ) -> None:
        """Place Pacgums everywhere except Pacman's position."""

        self.pacgums.clear()

        for y, row in enumerate(maze.grid):
            for x, cell in enumerate(row):
                if (x, y) != (pacman_x, pacman_y) and cell != 15:
                    self.add_pacgum(x, y)

    def generate_super_pacgums(self, maze: Maze) -> None:
        """Place Super-Pacgums in the four corners."""

        width = len(maze.grid[0])
        height = len(maze.grid)

        self.super_pacgums = {
            (0, 0),
            (width - 1, 0),
            (0, height - 1),
            (width - 1, height - 1),
        }

    def eat_super_pacgum(self, x: int, y: int) -> bool:
        """Remove a Super-Pacgum when Pac-Man eats it."""

        position = (x, y)

        if position in self.super_pacgums:
            self.super_pacgums.remove(position)
            return True

        return False
