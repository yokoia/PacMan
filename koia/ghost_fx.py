"""Ghost eye animation and maze-following return-home visual effects.

The four ghosts keep their original glossy artwork, movement, AI and
collisions. Gaze/blink frames are pre-rendered from the original artwork.
When a ghost is eaten, only its eyes fly home along a BFS path; the
existing respawn timer is extended just long enough to show that return.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import time

import pygame

from src.ghost import Ghost
from src.maze import Maze, NORTH, EAST, SOUTH, WEST
from src.pathfinding import bfs
from koia.polish import ArcadePolish


DIR_NAMES = {
    NORTH: "north",
    EAST: "east",
    SOUTH: "south",
    WEST: "west",
}
GHOST_NAMES = ("gpink", "gred", "gcyan", "gorange")
GHOST_COLORS = ((255, 94, 210), (255, 75, 76),
                (26, 231, 247), (255, 157, 47))


@dataclass
class ReturningEyes:
    """A short visual trip through the real maze toward the ghost spawn."""

    points: list[tuple[float, float]]
    duration: float
    elapsed: float = 0.0

    def advance(self, dt: float) -> None:
        """Advance the animation without depending on the frame rate."""
        self.elapsed = min(self.duration, self.elapsed + max(0.0, dt))

    def location(
        self, at_time: float | None = None
    ) -> tuple[tuple[float, float], str]:
        """Return an interpolated position and eye gaze along the path."""
        if len(self.points) < 2:
            return self.points[0], "north"
        segments = [math.dist(a, b)
                    for a, b in zip(self.points, self.points[1:])]
        whole = sum(segments)
        if whole < 0.01:
            return self.points[-1], "north"
        elapsed = self.elapsed if at_time is None else at_time
        progress = min(1.0, max(0.0, elapsed / max(0.01, self.duration)))
        distance_left = whole * progress
        for index, length in enumerate(segments):
            start = self.points[index]
            end = self.points[index + 1]
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            gaze = ("east" if dx > 0 else "west") if abs(dx) >= abs(dy) \
                else ("south" if dy > 0 else "north")
            if distance_left <= length or index == len(segments) - 1:
                fraction = min(1.0, distance_left / max(0.01, length))
                return ((start[0] + dx * fraction,
                         start[1] + dy * fraction), gaze)
            distance_left -= length
        return self.points[-1], "north"


class GhostMotion:
    """Animate original sprite eyes, blinks, bobs, and return-home eyes."""

    def __init__(self, assets_dir: Path, sprite_size: int = 44) -> None:
        """Load only small pre-rendered PNGs; no runtime art dependencies."""
        self.enabled = True
        self.sprite_size = sprite_size
        path = assets_dir / "ghost_motion"
        self.frames: dict[str, dict[str, pygame.Surface]] = {}
        for name in (*GHOST_NAMES, "gscared"):
            frames: dict[str, pygame.Surface] = {}
            for direction in (*DIR_NAMES.values(), "blink"):
                picture = pygame.image.load(
                    str(path / f"{name}_{direction}.png")
                ).convert_alpha()
                frames[direction] = pygame.transform.smoothscale(
                    picture, (sprite_size, sprite_size)
                )
            self.frames[name] = frames
        self.eyes = {
            direction: pygame.transform.smoothscale(
                pygame.image.load(
                    str(path / f"eyes_{direction}.png")
                ).convert_alpha(), (sprite_size, sprite_size)
            ) for direction in DIR_NAMES.values()
        }
        self.returning: dict[int, ReturningEyes] = {}
        self.respawn_flashes: dict[int, float] = {}
        self.respawn_centers: dict[int, tuple[float, float]] = {}
        self.demo_flight: ReturningEyes | None = None

    def reset(self) -> None:
        """Forget all visual animations when a level or life resets."""
        self.returning.clear()
        self.respawn_flashes.clear()
        self.respawn_centers.clear()
        self.demo_flight = None

    def start_demo(
        self, maze: Maze, cell_width: float, cell_height: float
    ) -> bool:
        """Show a visible return-to-spawn demo without changing gameplay.

        F6 uses a separate rendering-only ghost-eye journey. It never
        changes Ghost objects, player score, enemy AI, or collisions.
        """
        grid = maze.grid
        if not grid or not grid[0]:
            return False
        width, height = len(grid[0]), len(grid)
        home = (0, 0)
        corners = ((width - 1, height - 1), (0, height - 1),
                   (width - 1, 0))
        paths = [bfs(maze, start, home) for start in corners]
        choices = [path for path in paths if path and len(path) > 2]
        if not choices:
            return False
        path = max(choices, key=len)
        centers = [((x + 0.5) * cell_width, (y + 0.5) * cell_height)
                   for x, y in path]
        duration = max(2.7, min(5.2, (len(path) - 1) * 0.14))
        self.demo_flight = ReturningEyes(centers, duration)
        return True

    def _draw_eyes_flight(
        self, screen: pygame.Surface, flight: ReturningEyes,
        polish: ArcadePolish, demo: bool = False,
    ) -> None:
        """Draw glowing directional eyes and visible motion streaks."""
        center, gaze = flight.location()
        xy = (round(center[0]), round(center[1]))
        if polish.enabled:
            polish.glow(screen, xy, 24, (154, 236, 255), 100)
        for trail in range(5, 0, -1):
            behind, _ = flight.location(flight.elapsed - trail * 0.060)
            pygame.draw.circle(
                screen, (55 + (5-trail)*30, 154 + (5-trail)*18, 255),
                (round(behind[0]), round(behind[1])),
                max(1, (6 - trail)),
            )
        image = self.eyes[gaze]
        # No ghost body or surrounding outline: just the floating eyes.
        screen.blit(image, image.get_rect(center=xy))
        if demo:
            # The preview is isolated from the four actual ghosts.
            font = pygame.font.SysFont("monospace", 13, bold=True)
            label = font.render("EYES RETURN DEMO", True,
                                (255, 233, 114))
            text_xy = (xy[0], xy[1] - self.sprite_size // 2 - 18)
            screen.blit(label, label.get_rect(center=text_xy))

    def start_return(
        self,
        index: int,
        ghost: Ghost,
        position: pygame.Vector2,
        maze: Maze,
        cell_width: float,
        cell_height: float,
    ) -> None:
        """Start eyes-only flight and synchronize ghost's respawn delay.

        All pathfinding is visual only. Game logic still owns the ghost's
        eaten, frightened and collision states.
        """
        if index in self.returning or not ghost.eaten:
            return
        width = len(maze.grid[0])
        height = len(maze.grid)
        x = max(0, min(width - 1, int(position.x / cell_width)))
        y = max(0, min(height - 1, int(position.y / cell_height)))
        start = (x, y)
        spawn = (ghost.spawn_x, ghost.spawn_y)
        path = bfs(maze, start, spawn)
        if not path:
            # Unusual disconnected maze: still complete the visual respawn.
            path = [start, spawn]
        centers = [(float(position.x), float(position.y))]
        centers.extend(((px + 0.5) * cell_width,
                        (py + 0.5) * cell_height) for px, py in path)
        duration = min(3.3, max(0.80, (len(path) - 1) * 0.14))
        self.returning[index] = ReturningEyes(centers, duration)
        # The original code respawns in 0.8s, before eyes could travel.
        # Only lengthen this specific respawn, without touching chase AI.
        ghost.respawn_at = max(ghost.respawn_at,
                               time.monotonic() + duration + 0.16)

    def finish_return(
        self, index: int, spawn: tuple[float, float]
    ) -> None:
        """Start a brief respawn sparkle once the real ghost reappears."""
        self.returning.pop(index, None)
        self.respawn_flashes[index] = 0.50
        self.respawn_centers[index] = spawn

    def update(self, dt: float) -> None:
        """Advance animations using measured frame delta time."""
        # Return flight advances with real elapsed time even when a frame
        # stalls; otherwise the game respawn clock can finish before the
        # floating eyes reach home on a slower laptop.
        real_dt = max(0.0, dt)
        for flight in self.returning.values():
            flight.advance(real_dt)
        if self.demo_flight is not None:
            self.demo_flight.advance(real_dt)
            if self.demo_flight.elapsed >= self.demo_flight.duration:
                self.demo_flight = None
        for index in list(self.respawn_flashes):
            remaining = self.respawn_flashes[index] - real_dt
            if remaining <= 0:
                del self.respawn_flashes[index]
                self.respawn_centers.pop(index, None)
            else:
                self.respawn_flashes[index] = remaining

    def draw(
        self,
        screen: pygame.Surface,
        ghosts: list[Ghost],
        positions: list[pygame.Vector2],
        base_normal: list[pygame.Surface],
        base_scared: pygame.Surface,
        polish: ArcadePolish,
    ) -> None:
        """Paint animated ghosts and homing eyes at their visible positions."""
        seconds = pygame.time.get_ticks() / 1000.0
        for index, (ghost, pos) in enumerate(zip(ghosts, positions)):
            if ghost.eaten:
                flight = self.returning.get(index)
                if flight is not None:
                    self._draw_eyes_flight(screen, flight, polish)
                continue

            color = ((85, 151, 255) if ghost.frightened
                     else GHOST_COLORS[index % len(GHOST_COLORS)])
            moving = ghost.last_direction is not None
            phase = seconds * (7.8 if moving else 4.5) + index * 1.6
            bob = math.sin(phase) * (3.4 if self.enabled else 0.0)
            sway = math.sin(phase * 0.63) * (1.8 if self.enabled else 0.0)
            center = (round(pos.x + sway), round(pos.y + bob))
            if polish.enabled:
                polish.glow(screen, center, 27, color, 66)
            if not self.enabled:
                image = (base_scared if ghost.frightened
                         else base_normal[index])
                # Scale base art to the same size as animated frames.
                if image.get_width() != self.sprite_size:
                    image = pygame.transform.smoothscale(
                        image, (self.sprite_size, self.sprite_size))
            else:
                name = ("gscared" if ghost.frightened
                        else GHOST_NAMES[index])
                # Constant independent gaze animation: the eyes scan all
                # four cardinal directions, even while the ghost is idle.
                # A different phase for each ghost prevents synchronized
                # robot-like movement. The body still travels using AI.
                gaze_sequence = ("east", "south", "west", "north")
                gaze = gaze_sequence[
                    int((seconds + index * 0.31) / 0.47) % 4
                ]
                # Blink briefly; never hide the gaze for long.
                blink = (seconds + index * 0.71) % 3.5 < 0.16
                image = self.frames[name]["blink" if blink else gaze]
                # A slight squash/stretch makes the float legible at 60 FPS.
                squash = math.cos(phase) * 0.055
                width = max(20, round(self.sprite_size * (1 + squash)))
                height = max(20, round(self.sprite_size * (1 - squash)))
                image = pygame.transform.smoothscale(image, (width, height))
            screen.blit(image, image.get_rect(center=center))

        if self.demo_flight is not None:
            self._draw_eyes_flight(screen, self.demo_flight, polish,
                                   demo=True)

        if not polish.enabled:
            return
        for index, remaining in self.respawn_flashes.items():
            center = self.respawn_centers[index]
            progress = 1 - remaining / 0.50
            radius = round(5 + 21 * progress)
            alpha = round(175 * (1 - progress))
            diameter = 2 * radius + 8
            aura = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(aura, (170, 244, 255, alpha),
                               (diameter // 2, diameter // 2), radius, 2)
            pygame.draw.circle(aura, (255, 241, 156, alpha // 2),
                               (diameter // 2, diameter // 2),
                               max(2, radius // 3), 1)
            screen.blit(aura, (round(center[0]) - diameter // 2,
                               round(center[1]) - diameter // 2))
