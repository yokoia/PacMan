"""Small, optional presentation effects for the original Pac-Man artwork.

This module never changes movement, collisions, ghost AI, scoring, or levels.
"""

from dataclasses import dataclass
import math
import random

import pygame


Color = tuple[int, int, int]


@dataclass
class Particle:
    """One short-lived decorative spark."""

    x: float
    y: float
    vx: float
    vy: float
    lifetime: float
    age: float
    color: Color
    radius: int


@dataclass
class TrailLight:
    """A tiny fading light left behind the original Pac-Man sprite."""

    x: float
    y: float
    age: float = 0.0
    lifetime: float = 0.27


@dataclass
class ScorePopup:
    """Floating feedback for a score gain."""

    x: float
    y: float
    amount: int
    age: float = 0.0
    lifetime: float = 0.95


class ArcadePolish:
    """Draw lightweight glow, particles, and non-blocking notifications."""

    def __init__(self) -> None:
        """Prepare cached glow layers and a reusable score font."""
        self.enabled = True
        self.particles: list[Particle] = []
        self.popups: list[ScorePopup] = []
        self.glow_cache: dict[tuple[int, Color, int], pygame.Surface] = {}
        self.popup_font = pygame.font.SysFont("monospace", 21, bold=True)
        self.flash = 0.0
        self.trail: list[TrailLight] = []
        self._last_player_center: tuple[float, float] | None = None
        self._trail_distance = 0.0

    def glow(
        self,
        screen: pygame.Surface,
        center: tuple[int, int],
        radius: int,
        color: Color,
        strength: int = 65,
    ) -> None:
        """Blit a premade circular halo behind an existing game sprite."""
        if not self.enabled:
            return
        radius = max(2, int(radius))
        key = (radius, color, strength)
        halo = self.glow_cache.get(key)
        if halo is None:
            size = 2 * radius + 8
            halo = pygame.Surface((size, size), pygame.SRCALPHA)
            mid = size // 2
            pygame.draw.circle(
                halo, (*color, max(4, strength // 5)),
                (mid, mid), radius,
            )
            pygame.draw.circle(
                halo, (*color, max(8, strength // 3)),
                (mid, mid), max(1, int(radius * 0.69)),
            )
            pygame.draw.circle(
                halo, (*color, strength),
                (mid, mid), max(1, int(radius * 0.38)),
            )
            self.glow_cache[key] = halo
        screen.blit(halo, (center[0] - halo.get_width() // 2,
                           center[1] - halo.get_height() // 2))

    def burst(
        self,
        center: tuple[float, float],
        amount: int,
        color: Color = (255, 214, 77),
    ) -> None:
        """Add short-lived sparks and a points popup at Pac-Man's location."""
        if not self.enabled:
            return
        count = 10 if amount < 100 else 17
        for index in range(count):
            angle = 2 * math.pi * index / count + random.uniform(-0.2, 0.2)
            speed = random.uniform(48, 112)
            self.particles.append(Particle(
                center[0], center[1], math.cos(angle) * speed,
                math.sin(angle) * speed, random.uniform(0.33, 0.64),
                0.0, color, random.choice((2, 2, 3)),
            ))
        self.popups.append(ScorePopup(center[0], center[1] - 17, amount))
        self.particles = self.particles[-95:]
        self.popups = self.popups[-8:]

    def player_hit(self) -> None:
        """Give a gentle red flash after a lost life."""
        if self.enabled:
            self.flash = 0.38

    def reset_player_trail(self) -> None:
        """Avoid drawing a long streak after respawn or level changes."""
        self.trail.clear()
        self._last_player_center = None
        self._trail_distance = 0.0

    def track_player(self, center: tuple[float, float]) -> None:
        """Sample movement with a fixed gap, regardless of frame rate."""
        previous = self._last_player_center
        self._last_player_center = center
        if previous is None or not self.enabled:
            return
        dx = center[0] - previous[0]
        dy = center[1] - previous[1]
        distance = math.hypot(dx, dy)
        if distance == 0:
            return
        if distance > 48:
            # Teleport/respawn: don't draw a line across the whole maze.
            self.reset_player_trail()
            self._last_player_center = center
            return
        position = 9.0 - self._trail_distance
        while position <= distance:
            ratio = position / distance
            self.trail.append(TrailLight(
                previous[0] + dx * ratio,
                previous[1] + dy * ratio,
            ))
            position += 9.0
        self._trail_distance = (self._trail_distance + distance) % 9.0
        self.trail = self.trail[-32:]

    def draw_trail(self, screen: pygame.Surface) -> None:
        """Draw a subtle golden afterglow behind (not over) Pac-Man."""
        if not self.enabled:
            return
        for mark in self.trail:
            fade = max(0.0, 1.0 - mark.age / mark.lifetime)
            if fade <= 0:
                continue
            color = (round(255 * fade), round(174 * fade),
                     round(48 * fade))
            pygame.draw.circle(
                screen, color, (round(mark.x), round(mark.y)),
                max(1, round(3 * fade)),
            )

    def draw_power_surge(self, screen: pygame.Surface, active: bool) -> None:
        """Pulse a thin icy frame during power mode without hiding the maze."""
        if not (self.enabled and active):
            return
        seconds = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(seconds * 5.2) + 1) / 2
        blue = 117 + round(38 * pulse)
        pygame.draw.rect(
            screen, (48, blue, 250), screen.get_rect().inflate(-3, -3), 2,
            border_radius=9,
        )

    def update(self, dt: float) -> None:
        """Advance visual effects independently from the game's timers."""
        dt = min(0.1, max(0.0, dt))
        self.flash = max(0.0, self.flash - dt)
        for mark in self.trail:
            mark.age += dt
        self.trail = [mark for mark in self.trail
                      if mark.age < mark.lifetime]
        for item in self.particles:
            item.age += dt
            item.x += item.vx * dt
            item.y += item.vy * dt
            item.vy += 60 * dt
        self.particles = [p for p in self.particles if p.age < p.lifetime]
        for popup in self.popups:
            popup.age += dt
            popup.y -= 29 * dt
        self.popups = [p for p in self.popups if p.age < p.lifetime]

    def draw(self, screen: pygame.Surface) -> None:
        """Render effects over the original game scene."""
        if not self.enabled:
            return
        for p in self.particles:
            remaining = 1.0 - p.age / p.lifetime
            color = tuple(int(c * remaining) for c in p.color)
            pygame.draw.circle(
                screen, color, (round(p.x), round(p.y)),
                max(1, round(p.radius * remaining)),
            )
        for popup in self.popups:
            label = self.popup_font.render(
                f"+{popup.amount}", True, (255, 234, 105),
            )
            fade = 1 - popup.age / popup.lifetime
            label.set_alpha(max(0, int(255 * fade)))
            screen.blit(label, label.get_rect(center=(round(popup.x),
                                                      round(popup.y))))
        if self.flash > 0:
            layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            layer.fill((255, 43, 79, int(self.flash / 0.38 * 45)))
            screen.blit(layer, (0, 0))


def soft_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    fill: tuple[int, int, int, int] = (6, 11, 35, 194),
    border: Color = (132, 93, 237),
    radius: int = 16,
) -> None:
    """Paint a transparent dark-blue card without replacing backgrounds."""
    if rect.width <= 0 or rect.height <= 0:
        return
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, fill, layer.get_rect(), border_radius=radius)
    pygame.draw.rect(
        layer, (*border, 150), layer.get_rect(), 2,
        border_radius=radius,
    )
    surface.blit(layer, rect.topleft)


def glowing_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center: tuple[int, int],
    color: Color = (255, 219, 79),
) -> None:
    """Keep pixel-sharp text readable against colorful level backgrounds."""
    shadow = font.render(text, True, (7, 11, 38))
    screen.blit(shadow, shadow.get_rect(center=(center[0] + 2,
                                                center[1] + 3)))
    front = font.render(text, True, color)
    screen.blit(front, front.get_rect(center=center))
