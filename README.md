*This project has been created as part of the 42 curriculum by mseghrou, ykoia.*

# Pac-Man

## Description

Pac-Man is a Python arcade game inspired by the classic Pac-Man. The player navigates a generated maze, collects pacgums, and avoids ghosts. Super-pacgums temporarily make ghosts vulnerable, allowing the player to earn additional points.

The game combines object-oriented Python logic with a graphical interface built using Pygame. It includes 10 levels, configurable rules, a main menu, pause/resume controls, testing cheats, and persistent highscores.

## Instructions

### Requirements

- Python 3.10 or newer
- `make`, Python's `venv` module, and `pip`
- Project dependencies listed in `requirements.txt`
- The assigned A-Maze-ing wheel included in `packages/`
- For packaging: PyInstaller (installed through `requirements.txt`)
- For creating a release ZIP: the Linux `zip` command


### macOS: Pygame installation with Python 3.14

This project pins `pygame==2.6.1`. Use Python 3.13 for its prebuilt wheel on macOS;
otherwise pip may try to compile it and fail with `SDL.h file not found`.

If Homebrew Python 3.13 is installed, recreate any old Python 3.14 virtual environment:

```bash
brew install python@3.13
rm -rf .venv
"$(brew --prefix python@3.13)/bin/python3.13" -m venv .venv
.venv/bin/python --version  # Must say Python 3.13.x
make install
make run
```

`make run` does not reinstall dependencies; run `make install` first.

### Install and run from source

From the repository root, run:

```bash
make install
make run
```

`make install` creates a local `.venv` and installs dependencies, including the A-Maze-ing wheel from `packages/`. The Makefile uses `.venv/bin/python`, so manual virtual-environment activation is not required.

You can also launch the program directly:

```bash
.venv/bin/python pac-man.py config.json
```

Or, if all dependencies are installed for your system Python:

```bash
python3 pac-man.py config.json
```

When running from source, the program expects exactly one command-line argument: the path to a JSON configuration file.

To use a different configuration file:

```bash
make run CONFIG=custom.json
```

### Makefile commands

| Command | Purpose |
| --- | --- |
| `make install` | Create `.venv` and install project dependencies |
| `make run` | Launch the game with `config.json` |
| `make run CONFIG=custom.json` | Launch with another configuration file |
| `make debug` | Run the game with Python's debugger (`pdb`) |
| `make clean` | Remove Python and tooling caches outside `.venv` |
| `make lint` | Run Flake8 and Mypy checks |
| `make package` | Build the standalone game folder using `PacMan.spec` |
| `make zip` | Build the game and create `dist/PacMan-linux.zip` |

Run `make install` first in a fresh checkout.

### Build a downloadable Linux version

On Linux, run:

```bash
make install
make zip
```

`make zip` runs `make package` first, then creates the archive. The resulting files are:

```text
dist/
├── PacMan/
│   ├── PacMan
│   ├── config.json
│   ├── PLAY_INSTRUCTIONS.txt
│   ├── assets/
│   └── ... packaged dependencies
└── PacMan-linux.zip
```

To build only the unpacked executable folder, use `make package`. The PyInstaller build settings are stored in `PacMan.spec` in the repository root. The `build/` and `dist/` directories are generated artifacts and are not committed to Git.

The Linux build is intended for Linux systems; building on Linux does not generate Windows or macOS executables.

### Run the downloaded release

1. Download `PacMan-linux.zip` from the project's itch.io page
2. Extract the ZIP archive.
3. Open a terminal in the extracted `PacMan` directory.
4. Run:

```bash
chmod +x PacMan
./PacMan
```

The release contains `config.json` and `PLAY_INSTRUCTIONS.txt`. The bundled executable uses the included configuration by default. Edit `config.json` to customize the game.

Highscores are saved in `highscores.json` alongside the executable, so the extracted folder must be writable for score persistence.

### Controls

| Key | Action |
| --- | --- |
| Arrow keys / WASD | Move Pac-Man |
| `P` | Pause the game |
| `R` | Resume the game |
| `Esc` | Leave the current game or return from an instructions screen |
| `I` | Toggle increased movement speed (cheat) |
| `L` | Skip the current level (cheat) |
| `E` | Grant extra lives (cheat) |
| `F12` | Save an in-game screenshot to `screenshots/` |
| `F3` | Toggle optional glow, particles, trails, wall lights |
| `F4` | Cycle Aurora, Signature, Neon, and Classic wall styles |
| `F5` | Toggle animated ghost eyes, blinking, and floating movement |
| `F6` | Preview the returning-eyes animation without changing gameplay |
| `F7` | Whole maze / 1.25× / 1.50× player-following camera zoom |
| `F8` | Toggle fullscreen (when supported by the window system) |
| `M` | Toggle background music on/off |
| `N` | Toggle sound effects on/off |
| `-` / `+` (or `=`) | Lower / raise the background music volume |
| Up / Down + Enter | Navigate the main menu by keyboard |

The main menu allows players to start a game, view instructions, view highscores, and quit.

### Laptop-friendly display (15-inch screens)

The game has a **1000×800 logical playfield**, but the window is resizable
and Pygame can scale it to the available desktop space without changing
coordinates, walls, or collisions. On displays with a desktop height of
1000 pixels or less, gameplay starts at 1.25× zoom. Larger displays start
with the whole maze visible.

Press **F7** during gameplay to cycle 1.0× (whole maze), 1.25×, and 1.50×.
The close-up view smoothly follows Pac-Man and makes corridors, sprites,
and ghost eyes physically bigger. Score, Lives, Time, and Level stay
readable in a **text-only** strip across the top; there are no decorative
score boxes. In whole-maze view the original counters remain inside the
central 42-shaped artwork, also without boxes.

Press **F8** to toggle fullscreen if supported on your computer. You can
resize the window manually as well. The underlying maze still has the
same number of cells, and BFS, movement speeds, scoring, and collision
logic are not modified by visual zoom. For portfolio screenshots, use
1.0× to capture the entire maze; for a small display, use 1.25× or 1.50×.

All four ghosts continuously scan up, down, left, and right, even while
standing still. Eating a frightened ghost removes its body and leaves
**only its eyes** visible as they follow a BFS route to spawn. The colored
body reappears only when the return animation/respawn completes.

## Configuration

The game loads settings from the JSON file passed as its command-line argument. `ConfigLoader` also supports `#` comments outside quoted strings.

Example `config.json`:

```json
{
    "width": 15,
    "height": 15,
    "seed": 42,
    "lives": 3,
    "level_max_time": 90,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200
}
```

| Key | Default | Purpose |
| --- | ---: | --- |
| `width` | 15 | Initial maze width |
| `height` | 15 | Initial maze height |
| `seed` | 42 | Initial maze generation seed |
| `lives` | 3 | Starting lives |
| `level_max_time` | 90 | Initial time limit per level, in seconds |
| `points_per_pacgum` | 10 | Points for a regular pacgum |
| `points_per_super_pacgum` | 50 | Points for a super-pacgum |
| `points_per_ghost` | 200 | Points for eating a vulnerable ghost |

`ConfigLoader` reads the file, removes supported comments, parses JSON, validates types and accepted ranges, and supplies defaults for missing or invalid values. It warns about invalid settings, ignores unknown keys, and rejects duplicate JSON keys. Unreadable files produce a configuration error.

The supported value ranges are defined in `src/config.py` under `CONFIG_LIMITS`.

## Highscores

Highscores are saved to a local JSON file and reloaded when the game restarts. Each entry contains a player name and a non-negative integer score.

`HighscoreManager` validates, sorts, loads, and saves the **top 10 scores**. Names may contain letters, numbers, and spaces, with a maximum of 10 characters. Players can submit their results at the end of a game, and the same result cannot be submitted twice in one session.

JSON keeps the small leaderboard simple and avoids requiring an external database.

## Maze Generation

Mazes are generated using the assigned external **A-Maze-ing** package. `src/maze.py` integrates its `MazeGenerator` interface without modifying the package.

The generator receives maze dimensions and a seed, with `perfect=False` to allow loops and alternative routes. The generated grid is used for wall detection, movement, and drawing.

The first level uses the configured seed. Subsequent levels use new seeds and progressively larger mazes. The game contains **10 levels**.

## Implementation

The project separates game rules and state from Pygame rendering:

- `Game` manages levels, timers, collisions, points, pause/resume, and cheats.
- `Maze` wraps the external maze generator and provides wall and neighbor queries.
- `Entity` implements shared movement and wall-collision behavior.
- `Player` and `Ghost` inherit from `Entity` and provide specialized behavior.
- `PacgumManager` places and tracks regular and super-pacgums.
- `ConfigLoader` validates and loads game configuration.
- `HighscoreManager` manages saved leaderboard entries.
- `Menu` manages the main menu and navigation.
- `GameDrawing` renders the maze, sprites, and interface and processes player input.

Ghost movement uses maze connectivity and pathfinding. The rendering layer displays state updates produced by the game logic.

## General Software Architecture

```text
pac-man.py
    |
    +-- ConfigLoader (src/config.py)
    |
    +-- Menu (koia/menu.py)
            |
            +-- GameDrawing (koia/vis.py)
                    |
                    +-- Game (src/game.py)
                            |
                            +-- Maze (src/maze.py)
                            |     +-- A-Maze-ing MazeGenerator
                            |
                            +-- Entity (src/entity.py)
                            |     +-- Player (src/player.py)
                            |     +-- Ghost (src/ghost.py)
                            |
                            +-- PacgumManager (src/pacgum.py)
                            +-- HighscoreManager (src/highscore.py)
```

The entry point loads configuration and initializes Pygame. The menu launches `GameDrawing`, which interacts with `Game`. Core logic is organized in `src/`; interface code is organized in `koia/`.

## Project Management

Development responsibilities were divided between game logic and the Pygame interface, followed by integration and testing. The project management directory contains planning, task ownership, technical decisions, risks, test plans, and issue tracking:

[Project management documentation](project_management/)

Planned dates and actual completion dates are tracked separately.

## Resources

- [Python documentation](https://docs.python.org/3/) — Python and its standard library.
- [Pygame documentation](https://www.pygame.org/docs/) — graphics, events, and timing.
- [PyInstaller documentation](https://pyinstaller.org/en/stable/) — executable packaging.
- Assigned A-Maze-ing package — external maze generation dependency provided for this project.

### Use of AI tools

AI was used as a learning and review aid during development, including explanations of Python and object-oriented programming concepts, debugging integration, and discussing configuration validation, testing, and documentation structure. Suggested changes were reviewed and tested against the project code before use. Project decisions and implementation remain the team's responsibility.


## Signature Edition - visual polish

This update is built directly on the team's original validated version, rather
than replacing it with a different game. It preserves the original Pac-Man logo,
blue patterned menu, each level's custom background palette, the colorful ghost
assets, the central **42** scoreboard layout, and the existing game rules.

Presentation enhancements include: subtle wall and character glow; twinkling
Pac-Gums and animated power-ups; score popups, tiny spark bursts and a soft hit
flash; a short level-intro banner; a keyboard-accessible main menu; redesigned
pause, highscore, win and name-entry overlays using the same background assets.
The maze drawing is cached so the decorative wall glow is not rebuilt every frame.

The ghost AI, BFS, movement rules, scoring, level progression, highscores, and
configuration modules are **unchanged**. See `SIGNATURE_EDITION.md` for details.

**macOS setup:** If your `make install` fails while building `pygame==2.6.1`
under Python 3.14, create `.venv` with Python 3.13 and then run `make install`.
The repository includes `.python-version` set to `3.13`.


### Signature walls (previous visual refinement)

The original maze, 10 themed backgrounds, sprites and central 42 remain
unchanged. The previous Signature Walls release introduced the three styles
Signature, Neon and Classic. This release adds Aurora as the new default;
press **F4** to compare all four finishes. **F3** toggles optional effects
and **F12** saves a screenshot. The renderer in `koia/walls.py` never
modifies game logic.


## Signature Aurora — portfolio polish (visual-only)

This edition keeps the original sprites, original ten level backgrounds,
original 42-shaped HUD, maze generator, ghost AI and gameplay intact.
It adds a **fourth F4 wall mode**, **AURORA**, enabled by default:
rounded glass-neon tube walls with bright pearlescent centers and small,
slow-moving light reflections *following actual maze walls*. The wall
geometry is cached per maze/viewport and does not alter collision data.

The original Pac-Man now leaves a very short, subtle golden afterimage
while moving; Super Pacgums have orbiting sparks; and a blue outline pulses
while any ghost is frightened. The main menu also shows a tiny Pac-Man
chomping pellets using the original team's art.

- **F4**: AURORA → SIGNATURE → NEON → CLASSIC (purely visual).
- **F3**: toggle optional effects including wall streaks and player trail.
- **F12**: save a screenshot.

For a local Mac environment: use Python 3.13 if pygame 2.6.1 does not
install on a newer Python version.

See `AURORA_UPGRADE.md` for a file-by-file summary and testing limits.


## Ghost Motion Edition: animated eyes & homeward return

The original five glossy ghost sprites are still part of the game. Extra eye
frames in `assets/ghost_motion/` were derived from those same original images
so each ghost keeps the team's facial expression, palette and 3D look.

- Ghosts look in the direction they move, briefly blink, and float softly.
- When Pac-Man eats a frightened ghost, the body disappears and **only the
  original eyes** fly along a BFS route through the real maze back to spawn.
- The individual respawn timer is extended (up to about 3.5 seconds total)
  to allow the animated eyes to arrive before the original ghost reappears.
  This affects respawn timing only, not scoring, ghost AI, or collisions.
- At spawn the eyes disappear, the original ghost body appears, and a small
  arrival ring fades out.
- `F5` disables/enables moving pupils, blinking, and floating bob. Returning
  eyes remain visible for gameplay clarity. `F3` still toggles decorative FX.

Implementation: `koia/ghost_fx.py` handles animated sprite frames and visual
BFS routes; `koia/vis.py` integrates them in the existing game loop.
`src/` files and all original art files remain untouched. No additional
runtime Python packages are required. This build keeps the Python 3.13
Homebrew-compatible Makefile from Aurora Python Fix.

### Ghost Alive animation (visual-only update)

The original glossy ghosts now have noticeably larger moving eyes,
periodic blinks, a bouncy squash/stretch animation, and colored glows.
When a frightened ghost is eaten, the body disappears and the eyes
follow the maze corridors back to spawn with a visible light trail.
Press **F6** during gameplay to preview the eyes-only return without
changing the actual game, score, AI, or collisions. **F5** toggles
extra ghost motion. **F4** still cycles wall finishes.


## Signature Soundtrack Edition — original music

This edition retains the team's Pac-Man/ghost images, ten level
backgrounds, central **42** HUD, arcade walls, and the successful
pathfinding/ghost AI. No code in `src/` was changed.

The soundtrack consists of **four original synthesized chiptune loops**:

- **Star Chomp** — playful menu music.
- **Moonwalk Maze** — exploration tune for levels 1–5.
- **Night Run** — more energetic tune from level 6 onwards.
- **Power Rush** — activates automatically when ghosts become frightened.

It also includes custom chomp, ghost capture, power-up, level-complete,
last-ten-seconds warning, victory, loss, and menu sounds. Music pauses
when the game pauses; it switches back to the menu when a run ends.
There are no downloaded commercial tracks or external sound services.

**Controls:** `M` toggles music, `N` toggles sound effects, `-` and
`+` (or `=`) adjust background volume. The main menu shows a small
animated jukebox. The audio system gracefully disables itself if a
sound device is not available. When a Pygame build cannot open Vorbis
OGG files, it falls back to the included WAV versions.

**Source & customization:** `koia/audio.py` controls playback and
`assets/audio/` contains all ready-to-use audio files. The optional
`tools/generate_soundtrack.py` script shows the exact original note
patterns and synthesizer settings. Running this build script requires
`numpy` and `soundfile`, but **running the game does not**.

The Ghost Alive fixes from the earlier build are included too:
noticeably larger eye animation, animated menu ghosts, and an isolated
`F6` eyes-only homecoming demo. The scene switches and special effects
are purely presentational; the only prior nonvisual ghost adjustment
is the Ghost Motion feature's existing slight extension of the
respawn timer while eyes return home.
