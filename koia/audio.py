"""Original adaptive soundtrack and optional in-game sound effects.

Audio files are original; see the offline generator in tools/.
The game remains fully playable when SDL audio or a sound device is absent.
"""

from pathlib import Path
import math

import pygame


TRACKS = {
    "menu": ("menu_star_chomp.ogg", "STAR CHOMP"),
    "maze": ("maze_moonwalk.ogg", "MOONWALK MAZE"),
    "chase": ("maze_night_run.ogg", "NIGHT RUN"),
    "power": ("power_rush.ogg", "POWER RUSH"),
}
SOUNDS = (
    "ui_move", "ui_select", "chomp_a", "chomp_b", "power",
    "ghost_eat", "life_lost", "level_up", "victory", "game_over",
    "warning",
)


class ArcadeAudio:
    """Own all music and sound playback, including mute/volume controls."""

    def __init__(self, assets_dir: Path) -> None:
        """Try to open SDL audio without making it a gameplay requirement."""
        self.directory = assets_dir / "audio"
        self.ready = False
        self.music_on = True
        self.effects_on = True
        self.volume = 0.48
        self.scene = "menu"
        self._playing = ""
        self._paused = False
        self._chomp_variant = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16,
                                  channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
            for name in SOUNDS:
                sound = pygame.mixer.Sound(str(self.directory / f"{name}.wav"))
                sound.set_volume(.66 if name not in ("chomp_a", "chomp_b")
                                 else .39)
                self.sounds[name] = sound
            self.ready = True
        except (pygame.error, OSError, ValueError) as error:
            # Sound output is optional: e.g. CI machines have no speakers.
            print(f"Audio unavailable; game stays playable: {error}")
            self.ready = False

    @property
    def track_name(self) -> str:
        """Provide a readable track name for the animated menu widget."""
        return TRACKS.get(self.scene, ("", "SILENCE"))[1]

    def set_scene(self, scene: str) -> None:
        """Switch original music only when the musical situation changes."""
        if scene == self.scene and self._playing == scene:
            return
        self.scene = scene
        if not self.ready:
            return
        if not self.music_on or scene not in TRACKS:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass
            self._playing = ""
            return
        filename = TRACKS[scene][0]
        for candidate in (filename, filename.replace(".ogg", ".wav")):
            try:
                pygame.mixer.music.load(str(self.directory / candidate))
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(loops=-1, fade_ms=360)
                self._playing = scene
                self._paused = False
                return
            except (pygame.error, OSError):
                continue
        # Missing or unsupported tracks must never break the game.
        print(f"Audio track unavailable: {filename} (and WAV fallback)")
        self._playing = ""

    def play(self, sound_name: str) -> None:
        """Play an unobtrusive sound effect, respecting the SFX toggle."""
        if not self.ready or not self.effects_on:
            return
        try:
            sound = self.sounds.get(sound_name)
            if sound is not None:
                sound.play()
        except pygame.error:
            pass

    def chomp(self) -> None:
        """Alternate two short notes so eating dots feels rhythmic."""
        self._chomp_variant = not self._chomp_variant
        self.play("chomp_b" if self._chomp_variant else "chomp_a")

    def pause(self) -> None:
        """Pause the music along with gameplay without losing position."""
        if self.ready and self.music_on:
            try:
                pygame.mixer.music.pause()
                self._paused = True
            except pygame.error:
                pass

    def resume(self) -> None:
        """Resume the soundtrack from its exact paused position."""
        if self.ready and self.music_on and self._paused:
            try:
                pygame.mixer.music.unpause()
            except pygame.error:
                pass
        self._paused = False

    def handle_key(self, key: int) -> str | None:
        """M music, N effects, minus/plus volume; return a HUD message."""
        if key == pygame.K_m:
            self.music_on = not self.music_on
            # Using a separate _playing value allows re-enabling the current
            # track without resetting UI state or re-entering the scene.
            self._playing = ""
            self.set_scene(self.scene)
            return "MUSIC ON" if self.music_on else "MUSIC OFF"
        if key == pygame.K_n:
            self.effects_on = not self.effects_on
            return "SOUND FX ON" if self.effects_on else "SOUND FX OFF"
        if key in (pygame.K_MINUS, pygame.K_KP_MINUS,
                   pygame.K_EQUALS, pygame.K_KP_PLUS):
            delta = -.10 if key in (pygame.K_MINUS, pygame.K_KP_MINUS) else .10
            self.volume = min(1.0, max(0.0, round(self.volume + delta, 2)))
            if self.ready:
                try:
                    pygame.mixer.music.set_volume(self.volume)
                except pygame.error:
                    pass
            return f"MUSIC VOLUME {round(self.volume*100)}%"
        return None

    def draw_menu_widget(self, screen: pygame.Surface) -> None:
        """Show a tiny animated jukebox without replacing the team's menu."""
        rect = pygame.Rect(screen.get_width()-261, 522, 245, 137)
        glass = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glass, (7, 9, 41, 197), glass.get_rect(),
                         border_radius=15)
        pygame.draw.rect(glass, (123, 78, 215, 178), glass.get_rect(),
                         width=2, border_radius=15)
        screen.blit(glass, rect.topleft)
        label = pygame.font.SysFont("monospace", 13, bold=True)
        small = pygame.font.SysFont("monospace", 12)
        fg = (247, 221, 101) if self.music_on else (151, 148, 178)
        title = label.render("ORIGINAL SOUNDTRACK", True, fg)
        screen.blit(title, (rect.x+12, rect.y+12))
        name = small.render(self.track_name if self.music_on else "MUTED",
                            True, (207, 194, 255))
        screen.blit(name, (rect.x+12, rect.y+37))
        seconds = pygame.time.get_ticks() / 1000.0
        for index in range(13):
            level = (.4 + .6 * abs(math.sin(
                seconds*(4.0+index*.16) + index*.82)))
            height = round(5 + (17*level if self.music_on else 0))
            color = (255, 196, 105) if index % 3 == 0 else (148, 117, 249)
            pygame.draw.rect(screen, color, pygame.Rect(
                rect.x+12+index*17, rect.y+85-height, 9, height),
                border_radius=3)
        help_text = small.render("M music  N FX   - / + volume", True,
                                 (188, 186, 228))
        screen.blit(help_text, (rect.x+11, rect.y+105))
