try:
    from mazegenerator import MazeGenerator
except ModuleNotFoundError as error:
    if error.name == "mazegenerator":
        raise SystemExit(
            "Error: Required package 'mazegenerator' is missing.\n"
            "Run 'make install' to install project dependencies."
        ) from None
    raise

NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8


class Maze:
    """Manage maze generation and wall information"""

    def __init__(
            self,
            width: int,
            height: int,
            seed: int = 0,
            ) -> None:

        try:
            self.generator = MazeGenerator(
                size=(width, height),
                perfect=False,
                seed=seed,
            )
            self.grid: list[list[int]] = self.generator.maze

        except Exception as error:
            raise RuntimeError(
                f"Failed to generate maze: {error}"
            ) from None

    def has_wall(self, x: int, y: int, direction: int) -> bool:
        """Return True if a wall exists in the given direction."""
        cell = self.grid[y][x]
        return bool(cell & direction)

    def get_neighbors(self, x: int, y: int) -> list[tuple[int, int]]:
        """Return a list of neighboring cells that are accessible (no wall)."""
        neighbors = []
        directions = [
            (NORTH, (0, -1)),
            (EAST, (1, 0)),
            (SOUTH, (0, 1)),
            (WEST, (-1, 0))
        ]

        for direction, (dx, dy) in directions:
            if self.has_wall(x, y, direction):
                continue
            new_x = x + dx
            new_y = y + dy
            if 0 <= new_x < len(self.grid[0]) and 0 <= new_y < len(self.grid):
                neighbors.append((new_x, new_y))

        return neighbors
