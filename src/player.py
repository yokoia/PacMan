from src.entity import Entity


class Player(Entity):
    """Represent Pac-Man inside the maze."""

    def __init__(self, x: int, y: int, lives: int = 3) -> None:
        """Initialize Pac-Man's position and spawn point"""
        super().__init__(x, y)

        self.lives = lives
        self.score = 0

    def add_score(self, points: int) -> None:
        """Increase the player's score."""
        self.score += points

    def lose_life(self) -> None:
        """Decrease Pac-Man's remaining lives by one."""
        if self.lives > 0:
            self.lives -= 1

    def is_game_over(self) -> bool:
        """Return True when Pac-man has no lives left."""
        return self.lives == 0
