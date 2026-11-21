import math
import sys
import pygame
from pathlib import Path
from typing import TypedDict
from src.maze import NORTH, EAST, SOUTH, WEST
from src.game import Game
from src.highscore import HighscoreManager
from src.ghost import Ghost
from src.pacgum import PacgumManager
from koia.audio import ArcadeAudio
from koia.polish import ArcadePolish, glowing_text, soft_panel
from koia.walls import WALL_STYLES, WallEnergy, render_walls
from koia.ghost_fx import GhostMotion
from koia.camera import MazeCamera


LEVEL_THEMES = {
    1: {
        "background": "assets/background.png",
        "wall": "deepskyblue",
        "cell": "midnightblue",
    },
    2: {
        "background": "assets/level2.png",
        "wall": "chocolate",
        "cell": "peru",
    },
    3: {
        "background": "assets/level3.png",
        "wall": "turquoise",
        "cell": "teal",
    },
    4: {
        "background": "assets/level4.png",
        "wall": "hotpink",
        "cell": "mediumvioletred",
    },
    5: {
        "background": "assets/level5.png",
        "wall": "palegreen",
        "cell": "darkseagreen",
    },
    6: {
        "background": "assets/level6.png",
        "wall": "khaki",
        "cell": "goldenrod",
    },
    7: {
        "background": "assets/level7.png",
        "wall": "tomato",
        "cell": "brown",
    },
    8: {
        "background": "assets/level8.png",
        "wall": "violet",
        "cell": "darkmagenta",
    },
    9: {
        "background": "assets/level9.png",
        "wall": "mediumpurple",
        "cell": "darkviolet",
    },
    10: {
        "background": "assets/level10.png",
        "wall": "white",
        "cell": "mintcream",
    }
}


class GhostImages(TypedDict):
    normal: list[pygame.Surface]
    scared: pygame.Surface


class GameDrawing:
    def __init__(
        self, screen: pygame.Surface, audio: ArcadeAudio | None = None
    ) -> None:
        self.screen = screen
        self.audio = audio
        self.backgrounds: dict[int, pygame.Surface] = {}
        self.polish = ArcadePolish()
        self.wall_energy = WallEnergy()
        self._maze_cache_key: (
            tuple[int, int, tuple[int, int], str] | None
        ) = None
        self._maze_surface: pygame.Surface | None = None
        self.wall_style = "aurora"
        self.banner_started = pygame.time.get_ticks() / 1000.0
        self.notice_until = 0.0
        self.notice_text = ""
        self.hud_fonts: dict[int, pygame.font.Font] = {}
        self.ghost_motion: GhostMotion | None = None
        # A compact laptop starts zoomed in; large desktop screens show
        # the full maze. F7 can always switch between all three views.
        try:
            desktop_height = pygame.display.get_desktop_sizes()[0][1]
        except (AttributeError, IndexError, pygame.error):
            desktop_height = 1080
        self.camera = MazeCamera(1.25 if desktop_height <= 1000 else 1.0)
        self._world = pygame.Surface(self.screen.get_size()).convert()

    def draw_maze(self, level: int, maze_grid: list[list[int]]) -> None:
        """Draw the team's original maze with a selectable wall finish."""
        key = (level, id(maze_grid), self.screen.get_size(),
               self.wall_style)
        width, height = self.screen.get_size()
        theme = LEVEL_THEMES[level]
        if (self._maze_cache_key != key
                or self._maze_surface is None):
            if (level not in self.backgrounds
                    or self.backgrounds[level].get_size() != (width, height)):
                picture = pygame.image.load(theme["background"]).convert()
                self.backgrounds[level] = pygame.transform.smoothscale(
                    picture, (width, height)
                )
            base = self.backgrounds[level].copy()
            render_walls(base, maze_grid, theme["wall"], theme["cell"],
                         self.wall_style)
            self._maze_cache_key = key
            self._maze_surface = base
        self.screen.blit(self._maze_surface, (0, 0))
        self.wall_energy.draw(
            self.screen, maze_grid, theme["wall"],
            pygame.time.get_ticks() / 1000.0,
            self.polish.enabled and self.wall_style == "aurora",
        )

    def highscore_window(self) -> None:
        """Display original high scores over the original blue level art."""
        manager = HighscoreManager()
        manager.load_highscores()
        background = pygame.transform.smoothscale(
            pygame.image.load("assets/background.png").convert(),
            self.screen.get_size(),
        )
        heading = pygame.font.SysFont("monospace", 38, bold=True)
        font = pygame.font.SysFont("monospace", 26, bold=True)
        small = pygame.font.SysFont("monospace", 17)
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if (self.audio is not None and
                            self.audio.handle_key(event.key) is not None):
                        continue
                    if event.key == pygame.K_ESCAPE:
                        return
            self.screen.blit(background, (0, 0))
            soft_panel(
                self.screen, pygame.Rect(190, 95, 620, 640),
                (6, 10, 41, 227), (160, 100, 252), 25,
            )
            glowing_text(
                self.screen, heading, "HALL OF FAME", (500, 150)
            )
            glowing_text(
                self.screen, small, "TOP 10 HIGHSCORES", (500, 191),
                (197, 167, 255),
            )
            if not manager.scores:
                glowing_text(
                    self.screen, font, "Your legend starts here!",
                    (500, 420), (255, 226, 105),
                )
            for i, entry in enumerate(manager.scores[:10]):
                line_y = 241 + i * 43
                if i < 3:
                    soft_panel(
                        self.screen, pygame.Rect(230, line_y - 17, 540, 35),
                        (32, 23, 85, 170), (106, 73, 205), 8,
                    )
                rank = font.render(f"{i + 1:02d}", True, (196, 143, 255))
                name = font.render(
                    str(entry["name"])[:10], True, (255, 230, 123)
                )
                score = font.render(str(entry["score"]), True,
                                    (238, 244, 255))
                self.screen.blit(rank, (247, line_y - 13))
                self.screen.blit(name, (318, line_y - 13))
                self.screen.blit(
                    score, (733 - score.get_width(), line_y - 13)
                )
            glowing_text(
                self.screen, small, "ESC  -  RETURN TO MENU",
                (500, 704), (207, 192, 255),
            )
            pygame.display.flip()
            clock.tick(60)

    def draw_state(self, state: str, score: int) -> None:
        """Show final score with the classic logo and a gentle animation."""
        background = pygame.transform.smoothscale(
            pygame.image.load("assets/background.png").convert(),
            self.screen.get_size(),
        )
        logo = pygame.transform.smoothscale(
            pygame.image.load("assets/pacu.png").convert_alpha(),
            (550, 310),
        )
        big = pygame.font.SysFont("monospace", 53, bold=True)
        mid = pygame.font.SysFont("monospace", 34, bold=True)
        small = pygame.font.SysFont("monospace", 18)
        success = state != "game_over"
        title = "VICTORY!" if success else "GAME OVER"
        title_color = ((101, 252, 196) if success
                       else (255, 113, 143))
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if (self.audio is not None and
                            self.audio.handle_key(event.key) is not None):
                        continue
                    if event.key == pygame.K_RETURN:
                        return
            self.screen.blit(background, (0, 0))
            self.screen.blit(logo, logo.get_rect(center=(500, 133)))
            soft_panel(
                self.screen, pygame.Rect(180, 303, 640, 330),
                (6, 11, 40, 218), title_color, 24,
            )
            bob = round(math.sin(pygame.time.get_ticks() / 390) * 3)
            glowing_text(
                self.screen, big, title, (500, 391 + bob), title_color
            )
            glowing_text(
                self.screen, mid, f"FINAL SCORE   {score:,}",
                (500, 475), (255, 226, 105),
            )
            glowing_text(
                self.screen, small, "PRESS ENTER TO CONTINUE",
                (500, 570), (202, 187, 255),
            )
            pygame.display.flip()
            clock.tick(60)

    def draw_pacgums(
        self,
        pacgum_manager: PacgumManager,
        sp_image: pygame.Surface,
        cell_width: float,
        cell_height: float,
        maze_grid: list[list[int]]
    ) -> None:
        """Draw the original pellets and golden power-ups with soft sparkle."""
        seconds = pygame.time.get_ticks() / 1000.0
        for x, y in pacgum_manager.pacgums:
            if maze_grid[y][x] == 15:
                continue
            center = (round((x + 0.5) * cell_width),
                      round((y + 0.5) * cell_height))
            radius = 3 if (x + y) % 7 == 0 and math.sin(
                seconds * 2.7 + x + y) > 0.65 else 2
            pygame.draw.circle(
                self.screen, (255, 223, 95), center, radius
            )
        pulse = math.sin(seconds * 3.2)
        for x, y in pacgum_manager.super_pacgums:
            center = (round((x + 0.5) * cell_width),
                      round((y + 0.5) * cell_height))
            self.polish.glow(
                self.screen, center, 22, (255, 205, 61),
                58 + int(24 * (1 + pulse) / 2),
            )
            self.screen.blit(sp_image, sp_image.get_rect(center=center))
            if self.polish.enabled:
                # Two orbiting sparks signal that this is a power-up.
                for phase in (0.0, math.pi):
                    angle = seconds * 2.0 + phase + x * 0.3
                    spark = (round(center[0] + math.cos(angle) * 16),
                             round(center[1] + math.sin(angle) * 16))
                    pygame.draw.circle(self.screen, (255, 238, 132),
                                       spark, 2)

    def draw_pacman(
        self,
        image: pygame.Surface,
        pos: pygame.Vector2
    ) -> None:
        """Preserve the original Pac-Man sprite with a gentle yellow halo."""
        center = (round(pos.x), round(pos.y))
        self.polish.glow(self.screen, center, 19, (255, 205, 42), 35)
        self.screen.blit(image, image.get_rect(center=center))

    def draw_ghosts(
        self,
        ghost_images: GhostImages,
        poses: list[pygame.Vector2],
        ghosts: list[Ghost]
    ) -> None:
        """Show moving glossy eyes, blinking ghosts and returning eyes."""
        if self.ghost_motion is not None:
            self.ghost_motion.draw(
                self.screen, ghosts, poses, ghost_images["normal"],
                ghost_images["scared"], self.polish,
            )

    def pause_menu(self, game: Game) -> bool:
        """Pause with an overlay on the actual maze, not a different screen."""
        font = pygame.font.SysFont("monospace", 48, bold=True)
        small = pygame.font.SysFont("monospace", 20)
        if self.audio is not None:
            self.audio.pause()
        frozen = self.screen.copy()
        dark = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        dark.fill((4, 6, 29, 179))
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if (self.audio is not None and
                            self.audio.handle_key(event.key) is not None):
                        self.audio.pause()
                        continue
                    if event.key == pygame.K_r:
                        game.resume()
                        if self.audio is not None:
                            self.audio.resume()
                        return True
                    if event.key == pygame.K_ESCAPE:
                        if self.audio is not None:
                            self.audio.resume()
                        return False
            self.screen.blit(frozen, (0, 0))
            self.screen.blit(dark, (0, 0))
            soft_panel(
                self.screen, pygame.Rect(235, 285, 530, 220),
                (10, 12, 52, 222), (158, 104, 246), 24,
            )
            glowing_text(
                self.screen, font, "PAUSED", (500, 359),
                (255, 223, 97),
            )
            glowing_text(
                self.screen, small, "R  RESUME       ESC  QUIT",
                (500, 442), (208, 191, 255),
            )
            pygame.display.flip()
            clock.tick(60)

    def input_name(self, game: Game) -> None:
        """Enter a high-score name with the original ten-character rule."""
        name = ""
        title_font = pygame.font.SysFont("monospace", 35, bold=True)
        font = pygame.font.SysFont("monospace", 38, bold=True)
        small = pygame.font.SysFont("monospace", 18)
        clock = pygame.time.Clock()
        background = pygame.transform.smoothscale(
            pygame.image.load("assets/background.png").convert(),
            self.screen.get_size(),
        )
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif event.key == pygame.K_RETURN:
                        if name.strip():
                            game.save_player_score(name)
                            return
                    elif len(name) < 10:
                        if (event.unicode.isascii()
                                and (event.unicode.isalnum()
                                     or event.unicode == " ")):
                            name += event.unicode
            self.screen.blit(background, (0, 0))
            soft_panel(
                self.screen, pygame.Rect(160, 236, 680, 340),
                (5, 10, 44, 224), (167, 103, 251), 24,
            )
            glowing_text(
                self.screen, title_font, "ENTER YOUR NAME", (500, 314),
            )
            text = name + ("_" if pygame.time.get_ticks() // 500 % 2
                           else " ")
            glowing_text(
                self.screen, font, text or "_", (500, 406),
                (255, 228, 119),
            )
            glowing_text(
                self.screen, small, "MAX 10 CHARACTERS  |  ENTER TO SAVE",
                (500, 500), (204, 194, 255),
            )
            pygame.display.flip()
            clock.tick(60)

    def handle_events(
        self,
        running: bool,
        next_direction: int | None,
        game: Game
    ) -> tuple[bool, int | None]:
        """Handle game events and return the next direction"""

        buttons = {
            pygame.K_w: NORTH,
            pygame.K_d: EAST,
            pygame.K_s: SOUTH,
            pygame.K_a: WEST,
            pygame.K_UP: NORTH,
            pygame.K_RIGHT: EAST,
            pygame.K_DOWN: SOUTH,
            pygame.K_LEFT: WEST,
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                sound_notice = (
                    self.audio.handle_key(event.key)
                    if self.audio is not None else None
                )
                if sound_notice is not None:
                    self.notice_text = sound_notice
                    self.notice_until = (
                        pygame.time.get_ticks() / 1000 + 2.2
                    )
                    continue
                if event.key == pygame.K_F12:
                    screenshot_dir = Path("screenshots")
                    screenshot_dir.mkdir(exist_ok=True)
                    filename = (screenshot_dir /
                                f"pacman_{pygame.time.get_ticks()}.png")
                    try:
                        pygame.image.save(self.screen, str(filename))
                        self.notice_text = (
                            f"SCREENSHOT SAVED: {filename.name}"
                        )
                    except (OSError, pygame.error):
                        self.notice_text = "SCREENSHOT COULD NOT BE SAVED"
                    self.notice_until = pygame.time.get_ticks() / 1000 + 2
                elif event.key == pygame.K_F3:
                    self.polish.enabled = not self.polish.enabled
                    self.notice_text = ("EFFECTS ON" if self.polish.enabled
                                        else "EFFECTS OFF")
                    self.notice_until = pygame.time.get_ticks() / 1000 + 2
                elif event.key == pygame.K_F4:
                    current = WALL_STYLES.index(self.wall_style)
                    self.wall_style = WALL_STYLES[
                        (current + 1) % len(WALL_STYLES)
                    ]
                    self._maze_cache_key = None
                    self._maze_surface = None
                    self.notice_text = (
                        f"WALL STYLE: {self.wall_style.upper()}"
                    )
                    self.notice_until = pygame.time.get_ticks() / 1000 + 2
                elif event.key == pygame.K_F7:
                    zoom = self.camera.next_zoom()
                    self.notice_text = (
                        f"MAZE ZOOM {zoom:.2f}x  -  F7 TO CHANGE"
                    )
                    self.notice_until = pygame.time.get_ticks() / 1000 + 2.1
                elif event.key == pygame.K_F8:
                    try:
                        success = pygame.display.toggle_fullscreen()
                        self.notice_text = (
                            "DISPLAY MODE CHANGED" if success
                            else "FULLSCREEN NOT SUPPORTED HERE"
                        )
                    except pygame.error:
                        self.notice_text = "FULLSCREEN NOT SUPPORTED HERE"
                    self.notice_until = pygame.time.get_ticks() / 1000 + 2
                elif event.key == pygame.K_F5:
                    if self.ghost_motion is not None:
                        self.ghost_motion.enabled = (
                            not self.ghost_motion.enabled
                        )
                        self.notice_text = (
                            "GHOST ANIMATIONS ON" if self.ghost_motion.enabled
                            else "GHOST ANIMATIONS OFF"
                        )
                        self.notice_until = (
                            pygame.time.get_ticks() / 1000 + 2
                        )
                elif event.key == pygame.K_F6:
                    if self.ghost_motion is not None:
                        grid = game.maze.grid
                        cw = self.screen.get_width() / len(grid[0])
                        ch = self.screen.get_height() / len(grid)
                        started = self.ghost_motion.start_demo(
                            game.maze, cw, ch
                        )
                        self.notice_text = (
                            "GHOST EYES RETURN - VISUAL DEMO"
                            if started else "NO DEMO PATH AVAILABLE"
                        )
                        self.notice_until = (
                            pygame.time.get_ticks() / 1000 + 2.0
                        )
                elif event.key == pygame.K_l:
                    game.cheat_mode = True
                    game.activate_level_skip_cheat()
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_p:
                    game.pause()
                    running = self.pause_menu(game)
                    if not running:
                        break
                elif (event.key == pygame.K_RETURN
                      and game.state in ("game_over", "victory")):
                    running = False
                elif event.key == pygame.K_e:
                    game.cheat_mode = True
                    game.activate_extra_life_cheat()
                elif event.key == pygame.K_i:
                    game.cheat_mode = True
                    game.toggle_speed_cheat()
                elif game.state == "playing" and event.key in buttons:
                    next_direction = buttons[event.key]

        return running, next_direction

    def draw_score(
        self,
        text: str,
        value: int,
        maze_grid: list[list[int]],
        cell_width: float,
        cell_height: float
    ) -> None:
        """Draw the original center-42 scoreboard with no surrounding boxes."""
        maze_width = len(maze_grid[0])
        maze_height = len(maze_grid)
        pattern_col = (maze_width - 7) // 2
        pattern_row = (maze_height - 5) // 2
        if text == "level":
            score_col = pattern_col + 1
            score_row = pattern_row + 2
        else:
            row_offsets = {"score": 0, "time": 2, "lives": 4}
            score_col = pattern_col + 5
            score_row = pattern_row + row_offsets.get(text, 0)
        center = (round((score_col + 0.5) * cell_width),
                  round((score_row + 0.5) * cell_height))
        # Text only. The original 42-shaped score area remains visible;
        # no black/violet card or border hides its background artwork.
        font_size = round(min(21, max(13, min(
            cell_height * 0.45, cell_width * 0.33))))
        label = f"{text.upper()} {value}"
        if font_size not in self.hud_fonts:
            self.hud_fonts[font_size] = pygame.font.SysFont(
                "monospace", font_size, bold=True
            )
        font = self.hud_fonts[font_size]
        urgent = (text == "time" and value <= 10
                  and pygame.time.get_ticks() // 250 % 2 == 0)
        color = ((255, 101, 133) if urgent
                 else (255, 222, 100) if text == "score"
                 else (231, 232, 255))
        glowing_text(self.screen, font, label, center, color)

    def draw_zoom_hud(self, game: Game) -> None:
        """Keep all four counters visible even when the camera follows Pac-Man.

        The compact HUD is deliberately text-only, with no border or panel.
        It sits on the final picture rather than being cropped with the maze.
        """
        font = self.hud_fonts.get(22)
        if font is None:
            font = pygame.font.SysFont("monospace", 22, bold=True)
            self.hud_fonts[22] = font
        values = (
            ("SCORE", game.player.score, 128, (255, 222, 100)),
            ("LEVEL", game.current_level, 365, (220, 216, 255)),
            ("TIME", int(game.get_remaining_time()), 626,
             (255, 101, 133) if game.get_remaining_time() <= 10
             else (220, 216, 255)),
            ("LIVES", game.player.lives, 872, (220, 216, 255)),
        )
        for label, value, x, color in values:
            glowing_text(self.screen, font, f"{label} {value}",
                         (x, 25), color)

    def draw_level_banner(self, level: int) -> None:
        """A short, non-blocking celebratory label on each new level."""
        elapsed = pygame.time.get_ticks() / 1000 - self.banner_started
        if elapsed >= 1.7:
            return
        opacity = min(1.0, elapsed * 4.0, (1.7 - elapsed) * 3.0)
        if opacity <= 0:
            return
        banner = pygame.Surface((350, 88), pygame.SRCALPHA)
        pygame.draw.rect(
            banner, (8, 11, 42, int(195 * opacity)),
            banner.get_rect(), border_radius=18,
        )
        pygame.draw.rect(
            banner, (172, 118, 246, int(185 * opacity)),
            banner.get_rect(), 2, border_radius=18,
        )
        big = pygame.font.SysFont("monospace", 31, bold=True)
        small = pygame.font.SysFont("monospace", 15, bold=True)
        heading = big.render(f"LEVEL {level:02d}", True, (255, 224, 92))
        tagline = small.render("READY? LET'S CHOMP!", True,
                               (203, 187, 255))
        heading.set_alpha(round(255 * opacity))
        tagline.set_alpha(round(255 * opacity))
        banner.blit(heading, heading.get_rect(center=(175, 32)))
        banner.blit(tagline, tagline.get_rect(center=(175, 66)))
        # In close-up mode the score is a text-only strip at the top.
        # Move the intro below that strip, so both remain readable.
        self.screen.blit(banner, (325, 67 if self.camera.zoom > 1 else 10))

    def draw_notice(self) -> None:
        """Show a brief message after saving a screenshot or toggling FX."""
        if pygame.time.get_ticks() / 1000 > self.notice_until:
            return
        font = pygame.font.SysFont("monospace", 15, bold=True)
        rect = pygame.Rect(290, self.screen.get_height() - 45, 420, 32)
        soft_panel(self.screen, rect, (5, 9, 30, 234),
                   (133, 109, 229), 9)
        glowing_text(self.screen, font, self.notice_text, rect.center,
                     (239, 227, 127))

    def visualize_game(self, config: dict[str, int]) -> None:
        """Visualize the game using pygame"""

        pygame.display.set_caption("Pac-Man")
        clock = pygame.time.Clock()
        game = Game(config)
        if self.audio is not None:
            self.audio.set_scene("maze")
        maze_grid = game.maze.grid
        player = game.player
        cell_width = self.screen.get_width() / len(maze_grid[0])
        cell_height = self.screen.get_height() / len(maze_grid)
        # Pacman
        assets_dir = Path(__file__).resolve().parent.parent / "assets"
        self.ghost_motion = GhostMotion(
            assets_dir,
            sprite_size=max(28, min(47, round(min(
                cell_width, cell_height) * 0.82))),
        )
        pacman_images = {}
        for face in ("right", "left", "up", "down"):
            for mouth in ("closed", "open"):
                image = pygame.image.load(
                    str(assets_dir / f"pacman_{mouth}_{face}.png")
                ).convert_alpha()
                pacman_images[(face, mouth)] = pygame.transform.scale(
                    image, (28, 28))
        pos = pygame.Vector2(
            (player.x + 0.5) * cell_width,
            (player.y + 0.5) * cell_height)
        target = pos.copy()
        # moving variables
        direction = None
        next_direction = None
        animation_time = 0.0
        animation_frame = 0
        running = True
        # pacgums
        pacgum_manager = game.pacgum_manager
        sp_image = pygame.image.load("assets/mushroma.png").convert_alpha()
        sp_image = pygame.transform.scale(sp_image, (25, 25))
        # ghosts
        ghosts = game.ghosts
        ghost_speed_factors = game.ghost_speed_factors
        ghost_images: GhostImages = {
            "normal": [
                pygame.transform.scale(
                    pygame.image.load(name).convert_alpha(), (30, 30))
                for name in (str(assets_dir / "gpink.png"),
                             str(assets_dir / "gred.png"),
                             str(assets_dir / "gcyan.png"),
                             str(assets_dir / "gorange.png"))],
            "scared": pygame.transform.scale(
                    pygame.image.load(
                        str(assets_dir / "gscared.png")).convert_alpha(),
                    (30, 30))}
        poses = [pygame.Vector2((ghost.x + 0.5) * cell_width,
                                (ghost.y + 0.5) * cell_height)
                 for ghost in ghosts]
        targets = [pose.copy() for pose in poses]
        # collision
        original_collision_check = game.check_ghost_collisions
        # change this for game.update
        setattr(game, "check_ghost_collisions", lambda: None)
        last_invincible_until = game.invincible_until
        previous_score = game.player.score
        previous_lives = game.player.lives
        previous_ghost_eaten = [ghost.eaten for ghost in ghosts]
        previous_super_count = len(pacgum_manager.super_pacgums)
        previous_dot_count = len(pacgum_manager.pacgums)
        warned_on_level = -1

# ###################### Game Loop ######################################
        while running:
            dt = clock.tick(60) / 1000
            self.polish.update(dt)
            if self.ghost_motion is not None:
                self.ghost_motion.update(dt)

            game.update()
            if self.audio is not None:
                if len(pacgum_manager.super_pacgums) < previous_super_count:
                    self.audio.play("power")
                    self.notice_text = "POWER RUSH!  CHASE THE GHOSTS"
                    self.notice_until = pygame.time.get_ticks() / 1000 + 2
                elif len(pacgum_manager.pacgums) < previous_dot_count:
                    self.audio.chomp()
                previous_super_count = len(pacgum_manager.super_pacgums)
                previous_dot_count = len(pacgum_manager.pacgums)
                if (game.state == "playing"
                        and game.get_remaining_time() <= 10
                        and warned_on_level != game.current_level):
                    self.audio.play("warning")
                    self.notice_text = "HURRY! 10 SECONDS LEFT"
                    self.notice_until = pygame.time.get_ticks() / 1000 + 2
                    warned_on_level = game.current_level
            # When the real respawn timer finishes, show the ghost body
            # exactly at home, with a quick arrival sparkle.
            if self.ghost_motion is not None:
                for i, ghost in enumerate(ghosts):
                    if (i in self.ghost_motion.returning
                            and not ghost.eaten):
                        spawn = ((ghost.spawn_x + 0.5) * cell_width,
                                 (ghost.spawn_y + 0.5) * cell_height)
                        poses[i].update(spawn)
                        targets[i].update(spawn)
                        self.ghost_motion.finish_return(i, spawn)
# Handle all events.
            running, next_direction = self.handle_events(
                running, next_direction, game)
            if not running:
                break
# Ghosts moving
            for i, (ghostt, pose, targett) in enumerate(
                zip(ghosts, poses, targets)
            ):
                # An eaten ghost is rendered separately as returning eyes.
                if ghostt.eaten:
                    continue
                # Refresh the destination every frame (no stale cell target).
                targett.update(
                    (ghostt.x + 0.5) * cell_width,
                    (ghostt.y + 0.5) * cell_height)
                distance = pose.distance_to(targett)

                ghost_interval = (
                    game.ghost_move_interval * ghost_speed_factors[i]
                )

                if abs(targett.x - pose.x) > 0:
                    stepp = cell_width * dt / ghost_interval
                else:
                    stepp = cell_height * dt / ghost_interval

                if distance > 0:
                    pose += (targett - pose).normalize() * min(stepp, distance)
# pacman moving
            # Choose the next grid cell at the cell center.
            distance = pos.distance_to(target)
            if distance < 0.5:  # pixel
                pos.update(target)
                moved = False

                # Try the direction requested by the player first.
                if next_direction is not None:
                    old_x, old_y = player.x, player.y
                    player.move(next_direction, game.maze)
                    moved = (player.x != old_x or player.y != old_y)
                    if moved:
                        direction = next_direction
                        next_direction = None

                # If the requested direction is blocked,
                # keep moving in the previous direction.
                if not moved and direction is not None:
                    old_x, old_y = player.x, player.y
                    player.move(direction, game.maze)
                    moved = (player.x != old_x or player.y != old_y)

                # Calculate the destination in screen pixels.
                if moved:
                    target.update(
                        (player.x + 0.5) * cell_width,
                        (player.y + 0.5) * cell_height)

            distance = pos.distance_to(target)
            step = 4 * game.player_speed_multiplier

            if distance > 0:
                pos += (target - pos).normalize() * min(step, distance)

# Run the original backend collision rules at visible contact
            if game.state == "playing":
                for i, ghost in enumerate(ghosts):
                    hit = (
                        not ghost.eaten
                        and pos.distance_to(poses[i]) <= 20
                    )

                    setattr(
                        ghost,
                        "collides_with",
                        lambda player, hit=hit: hit
                    )

                try:
                    original_collision_check()
                finally:  # clear the temporary method
                    for ghost in ghosts:
                        delattr(ghost, "collides_with")
                # A newly eaten ghost keeps its current visible position.
                # Its eyes then follow the maze back to the spawn point.
                if self.ghost_motion is not None:
                    for i, ghost in enumerate(ghosts):
                        if ghost.eaten:
                            self.ghost_motion.start_return(
                                i, ghost, poses[i], game.maze,
                                cell_width, cell_height,
                            )
            # Reset visual positions after a collision
                if game.invincible_until != last_invincible_until:
                    if self.ghost_motion is not None:
                        self.ghost_motion.reset()
                    last_invincible_until = game.invincible_until
                    self.camera.reset_focus()

                    pos.update(
                        (player.x + 0.5) * cell_width,
                        (player.y + 0.5) * cell_height
                    )
                    target.update(pos)

                    direction = None
                    next_direction = None

                    for i, ghost in enumerate(ghosts):
                        poses[i].update(
                            (ghost.x + 0.5) * cell_width,
                            (ghost.y + 0.5) * cell_height)
                        targets[i].update(poses[i])
# Animation pictures
            if pos.distance_to(target) > 0.5:
                animation_time += dt
                if animation_time >= 0.12:
                    animation_frame = 1 - animation_frame
                    animation_time = 0.0
            else:
                animation_frame = 0
            # face direction
            facing = {
                NORTH: "up",
                EAST: "right",
                SOUTH: "down",
                WEST: "left",
            }.get(direction if direction is not None else EAST, "right")
            mouth = "open" if animation_frame else "closed"
            image = pacman_images[(facing, mouth)]

# Visual feedback only. Scoring, timing, and collision rules are unchanged.
            if self.audio is not None:
                for i, ghost in enumerate(ghosts):
                    if ghost.eaten and not previous_ghost_eaten[i]:
                        self.audio.play("ghost_eat")
                        self.notice_text = "GHOST CAPTURED!"
                        self.notice_until = (
                            pygame.time.get_ticks() / 1000 + 1.6
                        )
                previous_ghost_eaten = [ghost.eaten for ghost in ghosts]
                soundtrack = (
                    "power" if any(g.frightened and not g.eaten
                                   for g in ghosts)
                    else "chase" if game.current_level >= 6
                    else "maze"
                )
                if game.state == "playing":
                    self.audio.set_scene(soundtrack)
            if game.player.score > previous_score:
                self.polish.burst(
                    (pos.x, pos.y), game.player.score - previous_score
                )
            if game.player.lives < previous_lives:
                if self.audio is not None:
                    self.audio.play("life_lost")
                self.polish.player_hit()
                self.polish.reset_player_trail()
            previous_score = game.player.score
            previous_lives = game.player.lives

# Draaaaaaaaaaaaaawing #########################

            output_screen = self.screen
            if self.camera.zoom > 1.0:
                self.screen = self._world
            self.draw_maze(game.current_level, maze_grid)
            self.draw_pacgums(
                pacgum_manager,
                sp_image,
                cell_width,
                cell_height,
                maze_grid)
            self.polish.track_player((pos.x, pos.y))
            self.polish.draw_trail(self.screen)
            self.draw_pacman(image, pos)
            self.draw_ghosts(ghost_images, poses, ghosts)
            self.polish.draw(self.screen)
            self.polish.draw_power_surge(
                self.screen,
                any(ghost.frightened and not ghost.eaten
                    for ghost in ghosts),
            )
            self.screen = output_screen
            if self.camera.zoom > 1.0:
                focus = (pos.x, pos.y)
                # During an F6 demo, follow the flying eyes so they stay
                # visible even in the 1.50x close-up on a small laptop.
                if (self.ghost_motion is not None
                        and self.ghost_motion.demo_flight is not None):
                    focus, _ = self.ghost_motion.demo_flight.location()
                self.camera.draw(self._world, self.screen, focus, dt)
                self.draw_zoom_hud(game)
            else:
                for name, value in (
                    ("score", game.player.score),
                    ("lives", game.player.lives),
                    ("time", int(game.get_remaining_time())),
                    ("level", game.current_level),
                ):
                    self.draw_score(name, value, maze_grid,
                                    cell_width, cell_height)
            self.draw_level_banner(game.current_level)
            self.draw_notice()
            if game.state in ("game_over", "victory"):
                if self.audio is not None:
                    self.audio.set_scene("silence")
                    self.audio.play(
                        "victory" if game.state == "victory"
                        else "game_over"
                    )
                self.draw_state(game.state, game.player.score)
                self.input_name(game)
                return

# reseting for next level ########################
            if game.state == "level_complete":
                if self.audio is not None:
                    self.audio.play("level_up")
                game.start_next_level()
            if game.state == "playing" and maze_grid is not game.maze.grid:

                self.banner_started = pygame.time.get_ticks() / 1000.0
                self.polish.particles.clear()
                self.polish.popups.clear()
                self.polish.reset_player_trail()
                self.camera.reset_focus()
                if self.ghost_motion is not None:
                    self.ghost_motion.reset()
                maze_grid = game.maze.grid
                cell_width = self.screen.get_width() / len(maze_grid[0])
                cell_height = self.screen.get_height() / len(maze_grid)
                if self.ghost_motion is not None:
                    previous_enabled = self.ghost_motion.enabled
                    self.ghost_motion = GhostMotion(
                        assets_dir,
                        sprite_size=max(28, min(47, round(min(
                            cell_width, cell_height) * 0.82))),
                    )
                    self.ghost_motion.enabled = previous_enabled

                # Reset Pac-Man visual position
                player = game.player

                pos.update(
                    (player.x + 0.5) * cell_width,
                    (player.y + 0.5) * cell_height
                )
                target.update(pos)

                direction = None
                next_direction = None

                pacgum_manager = game.pacgum_manager
                ghosts = game.ghosts
                previous_super_count = len(pacgum_manager.super_pacgums)
                previous_dot_count = len(pacgum_manager.pacgums)
                previous_ghost_eaten = [g.eaten for g in ghosts]

                poses = [
                    pygame.Vector2(
                        (ghost.x + 0.5) * cell_width,
                        (ghost.y + 0.5) * cell_height
                    )
                    for ghost in ghosts
                ]

                targets = [pose.copy() for pose in poses]

                last_invincible_until = game.invincible_until
                animation_time = 0.0
                animation_frame = 0

            pygame.display.flip()
