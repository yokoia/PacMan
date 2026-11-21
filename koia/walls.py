"""Wall-only visual styles for the team's original maze.

All styles use the exact same maze wall bits and original level palettes.
The renderer draws onto a cached background; it never changes the grid,
player movement, collisions, scoring, or ghost pathfinding.
"""

from collections import defaultdict
import math

import pygame


Color = tuple[int, int, int]
Segment = tuple[tuple[int, int], tuple[int, int]]
WALL_STYLES = ("aurora", "signature", "neon", "classic")


def _mix(color: Color, other: Color, amount: float) -> Color:
    """Blend two RGB colors without depending on an extra package."""
    return (
        max(0, min(255, round(color[0] * (1 - amount)
                              + other[0] * amount))),
        max(0, min(255, round(color[1] * (1 - amount)
                              + other[1] * amount))),
        max(0, min(255, round(color[2] * (1 - amount)
                              + other[2] * amount))),
    )


def _merge_lines(
    horizontal: dict[int, list[tuple[int, int]]],
    vertical: dict[int, list[tuple[int, int]]],
) -> list[Segment]:
    """Join neighboring cell edges into continuous, clean wall strokes."""
    lines: list[Segment] = []
    for is_horizontal, groups in ((True, horizontal), (False, vertical)):
        for axis, intervals in groups.items():
            if not intervals:
                continue
            ordered = sorted(intervals)
            start, end = ordered[0]
            for next_start, next_end in ordered[1:]:
                if next_start <= end + 1:
                    end = max(end, next_end)
                else:
                    if is_horizontal:
                        lines.append(((start, axis), (end, axis)))
                    else:
                        lines.append(((axis, start), (axis, end)))
                    start, end = next_start, next_end
            if is_horizontal:
                lines.append(((start, axis), (end, axis)))
            else:
                lines.append(((axis, start), (axis, end)))
    return lines


def _maze_geometry(
    grid: list[list[int]], size: tuple[int, int]
) -> tuple[list[Segment], list[pygame.Rect]]:
    """Map maze bit flags to deduplicated wall lines and solid 42 blocks."""
    width, height = size
    if not grid or not grid[0]:
        return [], []
    cell_width = width / len(grid[0])
    cell_height = height / len(grid)
    horizontal: dict[int, list[tuple[int, int]]] = defaultdict(list)
    vertical: dict[int, list[tuple[int, int]]] = defaultdict(list)
    solid: list[pygame.Rect] = []

    for row, cells in enumerate(grid):
        for col, flags in enumerate(cells):
            x = round(col * cell_width)
            y = round(row * cell_height)
            right = round((col + 1) * cell_width)
            bottom = round((row + 1) * cell_height)
            if flags == 15:
                solid.append(pygame.Rect(x, y, right - x, bottom - y))
                continue
            if flags & 1:  # NORTH
                horizontal[y].append((x, right))
            if flags & 2:  # EAST
                vertical[right].append((y, bottom))
            if flags & 4:  # SOUTH
                horizontal[bottom].append((x, right))
            if flags & 8:  # WEST
                vertical[x].append((y, bottom))
    return _merge_lines(horizontal, vertical), solid


def _stroke(
    surface: pygame.Surface,
    segment: Segment,
    color: tuple[int, ...],
    width: int,
) -> None:
    """Draw a wall stroke with rounded end caps instead of square ends."""
    start, end = segment
    pygame.draw.line(surface, color, start, end, width)
    if width >= 3:
        radius = max(1, width // 2)
        pygame.draw.circle(surface, color, start, radius)
        pygame.draw.circle(surface, color, end, radius)


def _draw_classic(
    base: pygame.Surface, grid: list[list[int]], wall: Color,
) -> None:
    """Keep the Signature Edition's original 3px/6px wall appearance."""
    width, height = base.get_size()
    cw, ch = width / len(grid[0]), height / len(grid)
    glow = pygame.Surface((width, height), pygame.SRCALPHA)
    lines: list[tuple[tuple[int, int], tuple[int, int], int]] = []
    for row, cells in enumerate(grid):
        for col, flags in enumerate(cells):
            if flags == 15:
                continue
            x, y = round(col * cw), round(row * ch)
            right, bottom = round((col + 1) * cw), round((row + 1) * ch)
            if flags & 1:
                lines.append(((x, y), (right, y), 3))
            if flags & 2:
                lines.append(((right, y), (right, bottom), 6))
            if flags & 4:
                lines.append(((x, bottom), (right, bottom), 3))
            if flags & 8:
                lines.append(((x, y), (x, bottom), 6))
    for start, end, thickness in lines:
        pygame.draw.line(glow, (*wall, 42), start, end, thickness + 9)
    base.blit(glow, (0, 0))
    for start, end, thickness in lines:
        pygame.draw.line(base, wall, start, end, thickness)


def render_walls(
    base: pygame.Surface,
    grid: list[list[int]],
    wall_color: str,
    cell_color: str,
    style: str = "signature",
) -> None:
    """Paint a tasteful arcade tube outline without changing maze layout.

    aurora: dimensional tubes with a pearl highlight and living light.
    signature: softly rounded, double-highlight tube.
    neon: brighter outline inspired by classic glowing arcade cabinets.
    classic: exact wall line widths from the previous Signature Edition.
    """
    if not grid or not grid[0]:
        return
    wall_rgb = pygame.Color(wall_color)
    wall: Color = (wall_rgb.r, wall_rgb.g, wall_rgb.b)
    cell = pygame.Color(cell_color)
    segments, solid = _maze_geometry(grid, base.get_size())

    # The original solid "42" maze pattern remains identical in all modes.
    for rect in solid:
        pygame.draw.rect(base, cell, rect)

    if style == "classic":
        _draw_classic(base, grid, wall)
        return

    w, h = base.get_size()
    cell_size = min(w / len(grid[0]), h / len(grid))
    aurora = style == "aurora"
    neon = style == "neon"
    tube_ratio = 0.12 if (neon or aurora) else 0.10
    tube = max(4, min(9, round(cell_size * tube_ratio)))

    # The bloom is baked once into the cached maze, never per animation frame.
    bloom = pygame.Surface((w, h), pygame.SRCALPHA)
    if aurora:
        glow_layers = ((tube + 21, 13), (tube + 12, 31),
                       (tube + 6, 53))
    elif neon:
        glow_layers = ((tube + 23, 22), (tube + 13, 42),
                       (tube + 6, 66))
    else:
        glow_layers = ((tube + 17, 12), (tube + 9, 27),
                       (tube + 4, 42))
    for thickness, alpha in glow_layers:
        for segment in segments:
            _stroke(bloom, segment, (*wall, alpha), thickness)
    base.blit(bloom, (0, 0))

    # Navy sidewall, rich level color, and one tiny reflective highlight.
    # End caps make corners less blocky, but preserve every wall position.
    shadow = _mix(wall, (2, 6, 31), 0.82)
    face = _mix(wall, (255, 255, 255), 0.19 if aurora else
                (0.27 if neon else 0.12))
    highlight = _mix(wall, (255, 255, 255), 0.78 if aurora else
                     (0.83 if neon else 0.66))
    for segment in segments:
        _stroke(base, segment, shadow, tube + 3)
    for segment in segments:
        _stroke(base, segment, face, tube)
    for segment in segments:
        _stroke(base, segment, highlight, max(1, tube // 3))

    if aurora:
        # A razor-thin reflected core adds glass depth without a new maze
        # texture. Other wall styles remain exactly as they were.
        pearl = _mix(wall, (255, 251, 226), 0.90)
        for segment in segments:
            _stroke(base, segment, pearl, 1)


class WallEnergy:
    """Animate tiny light streaks along real walls without moving walls.

    Segment endpoints are cached when the maze or viewport changes.
    The animation draws only on the display; collisions and maze data
    are never touched. At most 28 small glow sprites are drawn per frame.
    """

    def __init__(self) -> None:
        """Create an empty geometry and glow cache."""
        self._key: tuple[int, tuple[int, int]] | None = None
        self._runners: list[Segment] = []
        self._glows: dict[Color, pygame.Surface] = {}

    def _refresh(self, grid: list[list[int]], size: tuple[int, int]) -> None:
        """Rebuild light positions only when the actual maze changes."""
        key = (id(grid), size)
        if key == self._key:
            return
        lines, _ = _maze_geometry(grid, size)
        # Sort for deterministic animation even across Python versions.
        valid = sorted(line for line in lines if math.dist(*line) > 18)
        count = min(28, len(valid))
        if count:
            self._runners = [valid[i * len(valid) // count]
                             for i in range(count)]
        else:
            self._runners = []
        self._key = key

    def _glow(self, color: Color) -> pygame.Surface:
        """Cache a tiny transparent halo in the current level palette."""
        sprite = self._glows.get(color)
        if sprite is None:
            sprite = pygame.Surface((30, 30), pygame.SRCALPHA)
            mid = (15, 15)
            pygame.draw.circle(sprite, (*color, 10), mid, 14)
            pygame.draw.circle(sprite, (*color, 25), mid, 9)
            pygame.draw.circle(sprite, (*color, 64), mid, 5)
            pygame.draw.circle(sprite, (255, 252, 231, 215), mid, 2)
            self._glows[color] = sprite
        return sprite

    def draw(
        self,
        screen: pygame.Surface,
        grid: list[list[int]],
        wall_color: str,
        seconds: float,
        enabled: bool,
    ) -> None:
        """Move a few discreet highlights on top of the static wall art."""
        if not enabled:
            return
        self._refresh(grid, screen.get_size())
        level = pygame.Color(wall_color)
        color: Color = (level.r, level.g, level.b)
        sprite = self._glow(color)
        for index, (start, end) in enumerate(self._runners):
            # Different phases/speeds avoid an artificial synchronized look.
            speed = 0.12 + (index % 5) * 0.016
            t = (seconds * speed + index * 0.217) % 1.0
            px = round(start[0] + (end[0] - start[0]) * t)
            py = round(start[1] + (end[1] - start[1]) * t)
            screen.blit(sprite, (px - 15, py - 15))

