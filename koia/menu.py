"""Original Pac-Man menu with subtle animation and keyboard support."""

import math
import sys
from pathlib import Path

import pygame

from koia.audio import ArcadeAudio
from koia.polish import glowing_text, soft_panel
from koia.vis import GameDrawing


class Menu:
    """Keep the original background, logo, colors, and four menu actions."""

    BUTTONS = (
        ("start", "PLAY", pygame.Rect(350, 340, 300, 70)),
        ("how", "HOW TO PLAY", pygame.Rect(350, 440, 300, 70)),
        ("scores", "HIGHSCORES", pygame.Rect(350, 540, 300, 70)),
        ("quit", "QUIT", pygame.Rect(350, 640, 300, 70)),
    )

    def __init__(self, screen: pygame.Surface, config: dict[str, int]) -> None:
        """Load the project's own assets once instead of every frame."""
        self.screen = screen
        self.config = config
        self.background = pygame.transform.smoothscale(
            pygame.image.load("assets/background.png").convert(),
            self.screen.get_size(),
        )
        self.logo = pygame.transform.smoothscale(
            pygame.image.load("assets/pacu.png").convert_alpha(),
            (700, 350),
        )
        self.ghosts = [
            pygame.transform.smoothscale(
                pygame.image.load(f"assets/{name}").convert_alpha(),
                (48, 48),
            ) for name in ("gpink.png", "gcyan.png", "gorange.png")
        ]
        # The same glossy ghosts now blink and glance around on the menu.
        # No replacement artwork: frames are derived from the original PNGs.
        self.ghost_frames: list[dict[str, pygame.Surface]] = []
        for name in ("gpink", "gcyan", "gorange"):
            frames = {}
            for gaze in ("north", "south", "east", "west", "blink"):
                path = f"assets/ghost_motion/{name}_{gaze}.png"
                frames[gaze] = pygame.transform.smoothscale(
                    pygame.image.load(path).convert_alpha(), (56, 56)
                )
            self.ghost_frames.append(frames)
        self.chomper = pygame.transform.smoothscale(
            pygame.image.load("assets/pacman_open_right.png").convert_alpha(),
            (29, 29),
        )
        self.title_font = pygame.font.SysFont("monospace", 31, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 18, bold=True)
        self.body_font = pygame.font.SysFont("monospace", 21)
        self.selected = 0
        self.clock = pygame.time.Clock()
        self.audio = ArcadeAudio(
            Path(__file__).resolve().parent.parent / "assets"
        )
        self.audio.set_scene("menu")

    def draw_menu(self) -> None:
        """Render the classic purple/yellow menu with animated highlights."""
        self.screen.blit(self.background, (0, 0))
        seconds = pygame.time.get_ticks() / 1000.0
        # The project logo remains the centerpiece.
        bob = int(math.sin(seconds * 1.6) * 5)
        self.screen.blit(
            self.logo, self.logo.get_rect(center=(500, 118 + bob)),
        )
        soft_panel(
            self.screen, pygame.Rect(320, 298, 360, 452),
            (5, 9, 39, 178), (116, 73, 215), 24,
        )
        glowing_text(
            self.screen, self.small_font, "THE ORIGINAL, LEVELLED UP",
            (500, 311), (186, 169, 255),
        )

        mouse = pygame.mouse.get_pos()
        for index, (_, caption, rect) in enumerate(self.BUTTONS):
            hovered = rect.collidepoint(mouse) or index == self.selected
            if hovered:
                pulse = int(14 * (1 + math.sin(seconds * 5)))
                color = (170 + pulse // 3, 107, 255)
                soft_panel(
                    self.screen, rect.inflate(10, 6),
                    (55, 25, 109, 226), color, 16,
                )
                pygame.draw.rect(
                    self.screen, (234, 185, 255), rect, 2,
                    border_radius=14,
                )
                marker_x = rect.x + 21
                pygame.draw.circle(
                    self.screen, (255, 220, 72),
                    (marker_x, rect.centery), 6,
                )
            else:
                soft_panel(
                    self.screen, rect, (14, 12, 61, 172),
                    (116, 69, 222), 14,
                )
            foreground = ((255, 145, 160) if caption == "QUIT"
                          else (255, 226, 94))
            glowing_text(
                self.screen, self.title_font, caption,
                rect.center, foreground,
            )

        # The original characters show clearly visible animations on MENU.
        for i, frames in enumerate(self.ghost_frames):
            gx = 170 + i * 64
            gy = 739 + round(math.sin(seconds * 5.0 + i * 1.6) * 5)
            eye_direction = ("east", "south", "west", "north")[
                (int(seconds * 1.6) + i) % 4
            ]
            blink = (seconds + i * 0.72) % 2.8 < 0.27
            image = frames["blink" if blink else eye_direction]
            stretch = round(math.sin(seconds * 5.0 + i * 1.6) * 2)
            image = pygame.transform.smoothscale(
                image, (56 + stretch, 56 - stretch)
            )
            self.screen.blit(image, image.get_rect(center=(gx, gy)))
        credit = self.small_font.render(
            "BY YKOIA & MSEGHROU  |  42 PROJECT", True, (216, 211, 255),
        )
        self.screen.blit(credit, credit.get_rect(center=(630, 779)))
        # A miniature playable-looking chomp animation uses the team's
        # own Pac-Man art. Dots reset naturally every animation cycle.
        path_start = 388
        chomp_x = path_start + (seconds * 48) % 265
        for i in range(7):
            dot_x = 404 + i * 32
            if dot_x > chomp_x + 6:
                pygame.draw.circle(
                    self.screen, (255, 221, 70), (dot_x, 743), 3,
                )
        self.screen.blit(self.chomper,
                         (round(chomp_x) - 14, 729))
        self.audio.draw_menu_widget(self.screen)

    def mouse_events(self, event: pygame.event.Event) -> str | None:
        """Return the menu action on a left mouse click."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, (action, _, rect) in enumerate(self.BUTTONS):
                if rect.collidepoint(event.pos):
                    self.selected = index
                    return action
        return None

    def generate_menu(self, logo: pygame.Surface) -> str | None:
        """Run a 60-FPS menu, retaining existing click behavior."""
        _ = logo  # Retained argument for compatibility with the old menu.
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.audio.handle_key(event.key) is not None:
                        continue
                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected = (self.selected + 1) % 4
                        self.audio.play("ui_move")
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.selected = (self.selected - 1) % 4
                        self.audio.play("ui_move")
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.audio.play("ui_select")
                        return self.BUTTONS[self.selected][0]
                    elif event.key == pygame.K_ESCAPE:
                        return "quit"
                if event.type == pygame.MOUSEMOTION:
                    for index, (_, _, rect) in enumerate(self.BUTTONS):
                        if rect.collidepoint(event.pos):
                            self.selected = index
                action = self.mouse_events(event)
                if action is not None:
                    self.audio.play("ui_select")
                    return action
            self.draw_menu()
            pygame.display.flip()
            self.clock.tick(60)

    def instructions_button(self) -> None:
        """Show original controls and rules on the familiar background."""
        heading = pygame.font.SysFont("monospace", 34, bold=True)
        body = pygame.font.SysFont("monospace", 19)
        details = (
            ("OBJECTIVE", (255, 184, 94)),
            ("Eat every Pac-Gum while avoiding ghosts!", (255, 233, 128)),
            ("", (255, 255, 255)),
            ("CONTROLS", (255, 184, 94)),
            ("ARROW KEYS / WASD   Move Pac-Man", (255, 233, 128)),
            ("P                   Pause", (255, 233, 128)),
            ("ESC                 Back / Quit", (255, 233, 128)),
            ("F4        Aurora / Signature / Neon / Classic",
             (198, 245, 255)),
            ("F3        Toggle glow + particles", (198, 245, 255)),
            ("F5        Toggle animated ghost eyes", (198, 245, 255)),
            ("F6        Preview returning ghost eyes", (198, 245, 255)),
            ("F7        Maze zoom: full / 1.25x / 1.50x",
             (198, 245, 255)),
            ("F8        Toggle fullscreen", (198, 245, 255)),
            ("M/N       Music / Sound FX on or off", (198, 245, 255)),
            ("-/+       Adjust music volume", (198, 245, 255)),
            ("F12       Save screenshot", (198, 245, 255)),
            ("", (255, 255, 255)),
            ("RULES", (255, 184, 94)),
            ("Collect all Pac-Gums to clear the maze.", (255, 233, 128)),
            ("Super Pac-Gums let you eat frightened ghosts.",
             (255, 233, 128)),
            ("Avoid dead ends and protect your lives!", (255, 233, 128)),
            ("", (255, 255, 255)),
            ("CHEATS (FOR THE 42 DEFENCE)", (255, 160, 180)),
            ("I  Speed   |   L  Skip level   |   E  Life", (255, 199, 208)),
        )
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.audio.handle_key(event.key) is not None:
                        continue
                    if event.key == pygame.K_ESCAPE:
                        return
            self.screen.blit(self.background, (0, 0))
            soft_panel(
                self.screen, pygame.Rect(110, 100, 780, 640),
                (5, 9, 37, 218), (143, 87, 247), 26,
            )
            glowing_text(
                self.screen, heading, "HOW TO PLAY", (500, 154),
            )
            y = 189
            for line, color in details:
                if not line:
                    y += 7
                    continue
                rendered = body.render(line, True, color)
                self.screen.blit(rendered, rendered.get_rect(center=(500, y)))
                y += 23
            glowing_text(
                self.screen, self.small_font,
                "PRESS ESC TO RETURN", (500, 705), (190, 169, 255),
            )
            pygame.display.flip()
            self.clock.tick(60)

    def activate_menu(self) -> None:
        """Preserve the original Play / How / Highscores / Quit workflow."""
        while True:
            self.audio.set_scene("menu")
            action = self.generate_menu(self.logo)
            if action == "start":
                drawing = GameDrawing(self.screen, self.audio)
                drawing.visualize_game(self.config)
            elif action == "how":
                self.instructions_button()
            elif action == "scores":
                drawing = GameDrawing(self.screen, self.audio)
                drawing.highscore_window()
            elif action == "quit":
                pygame.quit()
                sys.exit()
