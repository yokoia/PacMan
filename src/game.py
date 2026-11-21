from src.maze import Maze
from src.player import Player
from src.ghost import Ghost
from src.pacgum import PacgumManager
import time
import random
from src.highscore import HighscoreManager


class Game:
    """Manage the game's objects, rules, and state."""

    def __init__(self, config: dict[str, int]) -> None:
        self.config = config
        width = config["width"]
        height = config["height"]

        self.invincible_until = 0.0

        self.ghost_move_interval = 0.8

        self.ghost_speed_factors = [0.8, 1.15, 1, 1.20]

        self.ghost_last_moves = [
            time.monotonic() for _ in range(4)
        ]
        self.last_ghost_move = time.monotonic()

        self.maze = Maze(
            width,
            height,
            config["seed"]
        )

        player_x, player_y = self.find_player_spawn()

        self.player = Player(
            player_x,
            player_y,
            lives=config["lives"]
        )

        self.ghosts = [
            Ghost(0, 0),
            Ghost(width - 1, 0),
            Ghost(0, height - 1),
            Ghost(width - 1, height - 1)
        ]

        self.pacgum_manager = PacgumManager()

        self.pacgum_manager.generate_pacgums(
            self.maze,
            self.player.x,
            self.player.y
        )

        self.pacgum_manager.generate_super_pacgums(
            self.maze
        )

        self.pacgum_manager.pacgums.difference_update(
            self.pacgum_manager.super_pacgums
        )

        self.state = "playing"
        self.pause_started_at = 0.0

        self.level_max_time = config["level_max_time"]
        self.level_started_at = time.monotonic()

        self.current_level = 1
        self.total_levels = 10

        self.highscores = HighscoreManager()
        self.highscores.load_highscores()

        self.score_submitted = False

        self.cheat_mode = False
        self.extra_life_used = False

        self.player_speed_multiplier = 1.0

    def find_player_spawn(self) -> tuple[int, int]:
        width = len(self.maze.grid[0])
        height = len(self.maze.grid)

        center_x = width // 2
        center_y = height // 2

        if self.maze.get_neighbors(center_x, center_y):
            return center_x, center_y

        for distance in range(1, max(width, height)):
            for y in range(height):
                for x in range(width):
                    if (
                        center_x - distance <= x <= center_x + distance
                        and center_y - distance <= y <= center_y + distance
                    ):
                        if self.maze.get_neighbors(x, y):
                            return x, y

        raise ValueError("No playable position found")

    def collect_pacgums(self) -> None:
        x = self.player.x
        y = self.player.y

        if self.pacgum_manager.eat_pacgum(x, y):
            self.player.add_score(
                self.config["points_per_pacgum"]
            )

        if self.pacgum_manager.eat_super_pacgum(x, y):
            self.player.add_score(
                self.config["points_per_super_pacgum"]
            )

            for ghost in self.ghosts:
                if not ghost.eaten:
                    ghost.activate_frightened()

    def check_ghost_collisions(self) -> None:
        for ghost in self.ghosts:
            if ghost.eaten:
                continue

            if not ghost.collides_with(self.player):
                continue

            if ghost.frightened:
                self.player.add_score(
                    self.config["points_per_ghost"]
                )
                ghost.eat()
            elif time.monotonic() >= self.invincible_until:
                self.player.lose_life()

                if self.player.is_game_over():
                    self.state = "game_over"
                else:
                    # Reset Pac-Man
                    self.player.reset_position()

                    now = time.monotonic()
                    # Reset all ghosts
                    for ghost in self.ghosts:
                        ghost.reset_position()
                        ghost.deactivate_frightened()
                        ghost.eaten = False
                        ghost.respawn_at = 0.0

                        ghost.spawn_hold_until = now + 2.0

                    # Give Pac-Man 2 seconds of protection
                    self.invincible_until = now + 5.0
                    self.ghost_last_moves = [now for _ in self.ghosts]
                break

    def update(self) -> None:
        if self.state != "playing":
            return

        self.check_level_timeout()

        if self.state == "game_over":
            return

        self.collect_pacgums()
        self.check_level_win()
        if self.state == "level_complete":
            return

        self.check_ghost_collisions()

        if self.state == "game_over":
            return

        for ghost in self.ghosts:
            ghost.update_timers()

        current_time = time.monotonic()

        for i, ghost in enumerate(self.ghosts):
            if current_time < ghost.spawn_hold_until:
                continue

            interval = (
                self.ghost_move_interval * self.ghost_speed_factors[i]
            )

            if current_time - self.ghost_last_moves[i] >= interval:
                ghost.update_ghost(self.maze, self.player)
                self.ghost_last_moves[i] = current_time

        self.check_ghost_collisions()

    def pause(self) -> None:
        if self.state == "playing":
            self.state = "paused"
            self.pause_started_at = time.monotonic()

    def get_remaining_time(self) -> float:
        if self.state == "paused":
            current_time = self.pause_started_at
        else:
            current_time = time.monotonic()

        elapsed = current_time - self.level_started_at
        remaining = self.level_max_time - elapsed

        return max(0.0, float(remaining))

    def resume(self) -> None:
        if self.state == "paused":
            pause_duration = time.monotonic() - self.pause_started_at

            self.invincible_until += pause_duration
            self.ghost_last_moves = [
                last_move + pause_duration
                for last_move in self.ghost_last_moves
            ]
            self.level_started_at += pause_duration

            for ghost in self.ghosts:
                if ghost.frightened:
                    ghost.frightened_until += pause_duration

                if ghost.eaten:
                    ghost.respawn_at += pause_duration

                if ghost.spawn_hold_until > self.pause_started_at:
                    ghost.spawn_hold_until += pause_duration

            self.state = "playing"

    def check_level_timeout(self) -> None:
        if self.get_remaining_time() <= 0:
            self.state = "game_over"

    def check_level_win(self) -> None:
        if (
            not self.pacgum_manager.pacgums
            and not self.pacgum_manager.super_pacgums
        ):  # this for chech if ste is emptu if it return true
            self.state = "level_complete"

    def get_level_settings(self) -> tuple[int, int, int]:
        level = self.current_level

        width = self.config["width"] + (level - 1) * 2
        height = self.config["height"] + (level - 1) * 2
        max_time = self.config["level_max_time"] + (level - 1) * 20

        return width, height, max_time

    def start_next_level(self) -> None:
        if self.state != "level_complete":
            return

        if self.current_level >= self.total_levels:
            self.state = "victory"
            return

        self.current_level += 1

        width, height, max_time = self.get_level_settings()
        self.level_max_time = max_time

        new_seed = random.randint(0, 100000)

        self.maze = Maze(width, height, new_seed)

        player_x, player_y = self.find_player_spawn()

        self.player.spawn_x = player_x
        self.player.spawn_y = player_y

        self.player.reset_position()

        self.ghosts = [
            Ghost(0, 0),
            Ghost(width - 1, 0),
            Ghost(0, height - 1),
            Ghost(width - 1, height - 1)
        ]

        self.pacgum_manager = PacgumManager()

        self.pacgum_manager.generate_pacgums(
            self.maze,
            self.player.x,
            self.player.y)
        self.pacgum_manager.generate_super_pacgums(self.maze)

        self.pacgum_manager.pacgums.difference_update(
            self.pacgum_manager.super_pacgums
        )

        self.level_started_at = time.monotonic()
        self.ghost_last_moves = [
            self.level_started_at for _ in self.ghosts
        ]
        self.invincible_until = 0.0
        self.pause_started_at = 0.0

        self.state = "playing"

    def save_player_score(self, name: str) -> bool:
        """Save the player's score to the leaderboard."""

        if self.state not in ("game_over", "victory"):
            return False
        if self.score_submitted:
            return False

        success = self.highscores.add_score(name, self.player.score)

        if success:
            self.score_submitted = True

        return success

    def enable_cheat_mode(self) -> None:
        "Active cheats fir the current game."
        self.cheat_mode = True

    def activate_extra_life_cheat(self) -> bool:
        """Double Pac-Man's current lives."""

        if not self.cheat_mode:
            return False

        if self.state != "playing":
            return False

        if self.extra_life_used:
            return False
        self.player.lives *= 2
        self.extra_life_used = True

        return True

    def activate_level_skip_cheat(self) -> bool:
        """Skip the current level."""

        if not self.cheat_mode:
            return False

        if self.state != "playing":
            return False

        self.state = "level_complete"
        self.start_next_level()

        return True

    def toggle_speed_cheat(self) -> bool:
        """Toggle Pac-Man's speed boost."""

        if not self.cheat_mode:
            return False

        if self.state != "playing":
            return False

        if self.player_speed_multiplier == 1.0:
            self.player_speed_multiplier = 2.0
        else:
            self.player_speed_multiplier = 1.0

        return True
