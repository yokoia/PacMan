"""Optional camera zoom for laptops, without changing maze cell geometry.

Everything is still simulated and drawn in the game's original 1000x800
coordinate system. Only the final picture is cropped and enlarged, so the
maze, ghost collisions, AI and controls are never changed by the camera.
"""

from __future__ import annotations

import pygame


ZOOM_STEPS = (1.0, 1.25, 1.50)


def viewport_for(
    surface_size: tuple[int, int],
    focus: tuple[float, float],
    zoom: float,
) -> tuple[int, int, int, int]:
    """Return a clamped crop rectangle, even when focus is at an edge."""
    width, height = surface_size
    zoom = max(1.0, float(zoom))
    visible_width = max(1, min(width, round(width / zoom)))
    visible_height = max(1, min(height, round(height / zoom)))
    left = round(focus[0] - visible_width / 2)
    top = round(focus[1] - visible_height / 2)
    left = max(0, min(width - visible_width, left))
    top = max(0, min(height - visible_height, top))
    return (left, top, visible_width, visible_height)


class MazeCamera:
    """Render an optional player-following enlarged view of the same maze."""

    def __init__(self, initial_zoom: float = 1.0) -> None:
        self.zoom_index = min(
            range(len(ZOOM_STEPS)),
            key=lambda index: abs(ZOOM_STEPS[index] - initial_zoom),
        )
        self._focus: tuple[float, float] | None = None

    @property
    def zoom(self) -> float:
        """Active magnification factor."""
        return ZOOM_STEPS[self.zoom_index]

    def next_zoom(self) -> float:
        """Cycle through whole maze, close, and extra-close views."""
        self.zoom_index = (self.zoom_index + 1) % len(ZOOM_STEPS)
        self._focus = None
        return self.zoom

    def reset_focus(self) -> None:
        """Recenter immediately after respawn or a level transition."""
        self._focus = None

    def draw(
        self,
        source: pygame.Surface,
        destination: pygame.Surface,
        focus: tuple[float, float],
        dt: float,
    ) -> None:
        """Scale the selected world viewport to the original canvas size."""
        if self.zoom <= 1.0:
            destination.blit(source, (0, 0))
            return
        if self._focus is None:
            self._focus = focus
        else:
            follow = min(1.0, max(0.0, dt) * 9.0)
            self._focus = (
                self._focus[0] + (focus[0] - self._focus[0]) * follow,
                self._focus[1] + (focus[1] - self._focus[1]) * follow,
            )
        area = pygame.Rect(viewport_for(source.get_size(), self._focus,
                                        self.zoom))
        picture = pygame.transform.smoothscale(
            source.subsurface(area), destination.get_size(),
        )
        destination.blit(picture, (0, 0))
