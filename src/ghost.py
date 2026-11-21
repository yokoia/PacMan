from src.maze import NORTH, EAST, SOUTH, WEST, Maze
from src.player import Player
from src.pathfinding import bfs
import random
import time
from src.entity import Entity


class Ghost(Entity):
    """Represent a ghost inside the maze."""

    def __init__(self, x: int, y: int):
        super().__init__(x, y)

        self.frightened = False
        self.frightened_until = 0.0

        self.eaten = False
        self.respawn_at = 0.0

        self.last_direction: int | None = None

        self.spawn_hold_until = 0.0

        self.flee_reverse_pending = False

    def move(self, direction: int, maze: Maze) -> bool:
        """Move the ghost and remember its last direction."""

        moved = super().move(direction, maze)

        if moved:
            self.last_direction = direction

        return moved

    def get_valid_directions(self, maze: Maze) -> list[int]:
        """Return directions the ghost can move in."""

        directions: tuple[int, int, int, int] = (NORTH, EAST, SOUTH, WEST)
        valid = []

        for direction in directions:
            if self.can_move(direction, maze):
                valid.append(direction)

        return valid

    def choose_direction(self, maze: Maze) -> int | None:
        """Choose a random direction without unnecessary backtracking."""
        valid = self.get_valid_directions(maze)

        if not valid:
            return None

        opposite = {
            NORTH: SOUTH,
            SOUTH: NORTH,
            EAST: WEST,
            WEST: EAST
        }

        if self.last_direction is not None:
            backward = opposite[self.last_direction]

            options = [
                direction for direction in valid
                if direction != backward
            ]

            if options:
                valid = options

        return random.choice(valid)

    def collides_with(self, player: Player) -> bool:
        """Return true if the ghost and player share a position."""
        return self.x == player.x and self.y == player.y

    def reset_position(self) -> None:
        """Reset the ghost's position and last direction."""

        super().reset_position()
        self.last_direction = None
        self.flee_reverse_pending = False

    def can_detect_player(
        self,
        maze: Maze,
        player: Player,
        detection_range: int = 5,
    ) -> bool:

        """
        check whether Pac-Man is within detection range.
        """

        start = (self.x, self.y)
        target = (player.x, player.y)

        path = bfs(maze, start, target)

        if not path:
            return False

        distance = len(path) - 1

        return distance <= detection_range

    def get_chase_direction(self, maze: Maze, player: Player) -> int | None:
        """Find the next direction toward Pac-man using BFS."""
        path = bfs(maze, (self.x, self.y), (player.x, player.y))

        if not path or len(path) < 2:
            return None

        next_x, next_y = path[1]

        dx = next_x - self.x
        dy = next_y - self.y

        if dx == 1:
            return EAST
        if dx == -1:
            return WEST
        if dy == 1:
            return SOUTH
        if dy == -1:
            return NORTH

        return None

    def update_timers(self) -> None:
        self.update_respawn()
        self.update_frightened()

    def update_ghost(self, maze: Maze, player: Player) -> None:
        """
        Choose between chasing Pac-Man and moving radomly.
        """
        if self.eaten:
            return

        if self.frightened:
            direction = self.get_flee_direction(maze, player)
        elif self.can_detect_player(maze, player):
            direction = self.get_chase_direction(maze, player)
        else:
            direction = self.choose_direction(maze)

        if direction is not None:
            self.move(direction, maze)

    def activate_frightened(self, duration: float = 6.0) -> None:
        if not self.frightened:
            self.flee_reverse_pending = True

        self.frightened = True
        self.frightened_until = time.monotonic() + duration

    def deactivate_frightened(self) -> None:
        self.frightened = False
        self.frightened_until = 0.0
        self.flee_reverse_pending = False

    def update_frightened(self) -> None:
        if self.frightened and time.monotonic() >= self.frightened_until:
            self.deactivate_frightened()

    def eat(self, respawn_delay: float = 0.8) -> None:
        self.eaten = True
        self.frightened = False
        self.frightened_until = 0.0
        self.respawn_at = time.monotonic() + respawn_delay

    # update ghost position
    def update_respawn(self) -> None:
        """Respawn the ghost and keep it still for 2 seconds."""
        if self.eaten and time.monotonic() >= self.respawn_at:
            self.reset_position()
            self.eaten = False
            self.respawn_at = 0.0

            self.spawn_hold_until = time.monotonic() + 2.0

    def get_flee_direction(
        self,
        maze: Maze,
        player: Player
    ) -> int | None:
        """Flee from Pac-Man without oscillating between two cells."""

        directions = self.get_valid_directions(maze)

        if not directions:
            return None

        opposite = {
            NORTH: SOUTH,
            SOUTH: NORTH,
            EAST: WEST,
            WEST: EAST
        }

        offsets = {
            NORTH: (0, -1),
            EAST: (1, 0),
            SOUTH: (0, 1),
            WEST: (-1, 0)
        }

        # Reverse once when frightened mode starts.
        if self.flee_reverse_pending:
            self.flee_reverse_pending = False

            if self.last_direction is not None:
                backward = opposite[self.last_direction]

                if backward in directions:
                    return backward

        # After the initial reversal, avoid going back
        # unless there is no other valid direction.
        if self.last_direction is not None:
            backward = opposite[self.last_direction]

            alternatives = [
                direction for direction in directions
                if direction != backward
            ]

            if alternatives:
                directions = alternatives

        best_directions = []
        max_distance = -1

        for direction in directions:
            dx, dy = offsets[direction]

            new_x = self.x + dx
            new_y = self.y + dy

            path = bfs(
                maze,
                (new_x, new_y),
                (player.x, player.y)
            )

            if not path:
                continue

            distance = len(path) - 1

            if distance > max_distance:
                max_distance = distance
                best_directions = [direction]

            elif distance == max_distance:
                best_directions.append(direction)

        if best_directions:
            return random.choice(best_directions)

        return random.choice(directions)
