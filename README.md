*This activity has been created as part of the 42 curriculum by mal-jama, mewaysi.*

# Pac-Man 42

## Description

Pac-Man 42 is a complete keyboard-operated maze-chase game for Linux, written
in Python 3.10+ with a graphical pygame frontend. Clear ten increasingly large
mazes, collect ordinary and power pellets, escape four pursuing ghosts, and
record your score in a persistent top-ten leaderboard. The supplied
`mazegenerator` 2.1.0 wheel generates every maze without application patches.

The main menu offers Start Game, View Highscores, Instructions and Exit, with
leading scores also visible directly on that menu. Its animated twilight
garden includes swaying foliage, a softly lit path, floating fireflies and
pond ripples, with dark cards preserving readable navigation. A run follows
this flow:

```text
Main Menu -> Start Game -> Playing -> Victory / Game Over
          -> Enter Name -> Save Highscore -> Main Menu
```

Pause provides Resume and Return to Main Menu; returning requires a second
confirmation because it discards the unfinished run. The HUD shows score,
lives, level, remaining time and remaining collectibles throughout gameplay.
There is no sound requirement, network dependency during play, or downloaded
game artwork. Shapes and character images are rasterized by the application;
text uses pygame's bundled default font.

## Instructions

### Install and launch from source

Use a Linux graphical desktop with Python 3.10 or newer, `venv`, `pip` and
`make`. The logical window is 1000 by 850 pixels and scales coordinates, shapes
and text to the desktop, down to a 640 by 544 pixel window. Installation
creates a local `.venv` and installs pinned development/runtime
dependencies, including the byte-identical assigned wheel from `vendor/`.

```bash
make install
source .venv/bin/activate
python3 pac-man.py config.json
```

The program accepts **exactly one argument**, a configuration path. Relative
paths are relative to the launching shell. Its basename and extension are
unrestricted; the contents must be a JSON object, optionally with whole-line
hash comments. Missing or extra arguments print a short usage message and exit
with status 2. An unreadable file, broken JSON or non-object JSON root also
exits clearly with status 2. Display or dependency startup failures exit with
status 1. Unexpected runtime failures also exit with status 1 after recording
details. The console shows a short explanation; full tracebacks go to the log.

### Error diagnostics

Warnings and errors are saved automatically to
`$XDG_DATA_HOME/forty-two-pacman/errors.log`, or
`~/.local/share/forty-two-pacman/errors.log` when XDG_DATA_HOME is absent or
relative. This includes configuration repairs, score-file problems, maze
generation failures, display/dependency startup errors and unexpected runtime
exceptions. Each record includes a UTC timestamp, severity and module; caught
exceptions retain their full traceback in the file. Logging starts before
configuration is loaded and closes on every exit path.

The log rotates at 1 MiB, keeping three older files (`errors.log.1` through
`errors.log.3`). Logs use user data even if the game installation is read-only.
If file logging becomes unavailable, a console warning and a visible message
on the menu/end screen explain the problem; gameplay and score saving remain
available. Logging never redirects stdout/stderr or changes the score format.
If the active configuration occupies a log or backup path, diagnostics choose
`errors-2.log` (or the next non-conflicting name) to preserve that configuration.

### Controls and rules

| Context | Keys | Action |
| --- | --- | --- |
| Menus | Up/Down or W/S | Change selection |
| Menus | Enter or Space | Confirm |
| Main menu | Esc | Exit |
| Instructions / Highscores | Esc, Enter or Space | Return to main menu |
| Playing | Arrows or WASD | Move; turns are buffered at intersections |
| Playing | Esc or P | Pause |
| Pause | Esc or P | Resume; cancel an open discard confirmation first |
| End screen | Letters, digits, spaces | Enter a name, at most 10 characters |
| End screen | Backspace | Delete one character |
| End screen | Enter | Save the entered nonblank name and return to menu |
| End screen | Esc | Save as `PLAYER` and return to menu |
| Any screen | Window close | Quit |

Both **ordinary pellets and the four power pellets** must be eaten to complete
a level. Ordinary pellets award 10 points by default, power pellets 50, and
edible ghosts 200. A power pellet makes ghosts blue and edible for 8 seconds;
flashing during the final 2 seconds warns that the effect is ending. Eaten
ghosts become harmless eyes that travel through existing passages back to
their own corner. Eyes wait there until the full 7-second cooldown has passed,
then the ghost body returns. Return travel adapts to the route length to fit
inside that cooldown; it does not change normal ghost speed. Touching eyes
never removes lives or awards another capture.

An unpowered ghost contact removes one life. The player respawns near the
middle with 2 seconds of protection; active ghosts return home, power is
cleared, and the score, remaining items and countdown are retained. The same
contact cannot remove several lives in one update. New levels also begin with
2 seconds of protection. A timeout ends the run as a loss. Clearing the final
level shows Victory in a golden garden with a trophy and drifting leaves;
losing the final life shows Game Over in a moonlit garden with soft rain.
Both screens retain the final score and the same name-entry controls. Score
and lives carry between levels. Every new run resets gameplay and cheats
completely.

Pause freezes movement and **all gameplay timers**, including countdown,
power, eaten-ghost respawns, protection and speed boost. Decorative UI animation
can continue. Closing the window or confirming abandonment of a live run does
not record an unfinished score. Completed wins and losses record once when
name entry is confirmed; Esc explicitly records `PLAYER`.

### Review mode

Press **F1 during play** to toggle review mode. The HUD displays its status and
controls. These actions are available only while review mode is enabled:

| Key | Action |
| --- | --- |
| I | Toggle immunity to ghost contact |
| N | Complete this level immediately; the final skip produces Victory |
| G | Freeze/unfreeze ghost movement; respawn timers continue |
| L | Add one life, up to the review limit of 999 |
| B | Give a 1.75x player speed boost for 10 gameplay seconds |
| O | Activate/reset the configured power-up duration |
| C | Leave one ordinary pellet for a quick completion check |
| T | Reduce the countdown to at most 1 second to test timeout |
| K | Remove one life deliberately, including when I is enabled |

G also freezes returning eyes. Their cooldown still counts down, but a ghost
stays harmless until it has actually reached home after unfreezing. Pause
freezes both eye travel and the cooldown.

Turning review mode off clears its immunity, ghost freeze and speed boost.
Awarded lives, already earned points and actions already performed remain.
All completed runs, **including runs using cheats**, are eligible for the same
local leaderboard. This is an explicit review-friendly policy.

### Makefile and verification

| Command | Purpose |
| --- | --- |
| `make install` | Create `.venv`; install pinned requirements and original wheel |
| `make run` | Launch using `config.json` |
| `make run CONFIG=config.comments.json` | Launch an alternative configuration |
| `make debug CONFIG=config.json` | Run the same entry point under `pdb` |
| `make lint` | Run the exact subject-required flake8/mypy commands |
| `make lint-strict` | Run flake8 and `mypy . --strict` |
| `make test` | Run developer tests in `dev_tests/` |
| `make smoke` | Run the real frontend with SDL's dummy video driver |
| `make release` | Build and archive the Linux standalone distribution |
| `make clean` | Remove known build/type/test caches and bytecode |

`CONFIG=...` is supported by run, debug and smoke. `PYTHON` and `VENV` may be
overridden for installation/tooling. Clean preserves sources, configuration,
all user scores, original archives, original/vendor wheels, `dist/` and
`release/`. Developer tests are separate from game runtime and excluded from
the packaged release; they are not presented as graded submission programs.

The mandatory lint target executes:

```bash
flake8 .
mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

For an isolated full application diagnostic, activate the virtual environment
and use a fresh temporary score directory:

```bash
XDG_DATA_HOME="$(mktemp -d)" SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PACMAN_SMOKE_TEST=1 python3 pac-man.py config.json
```

The diagnostic uses the actual graphics adapter and model, follows valid maze
paths to clear level one, skips the remaining levels, saves/reloads a score,
checks timeout loss and visits the menus. It deliberately uses review tools
and an extended first-level diagnostic timer. It is not evidence of an
unassisted human playthrough. Optional `PACMAN_SCREENSHOTS=<directory>` captures
the rendered screens during this diagnostic.

Validation on the build host: **152 developer tests passed**; required
`make lint` and optional `make lint-strict` passed. Source and standalone
headless diagnostics completed all ten levels, name entry, persistence and
menu reuse. See [acceptance_tests.md](project_management/acceptance_tests.md)
for exact checks, actual evidence and the limits of automated play.

### Package and distribute

```bash
make release
tar -xzf release/Pacman42-Linux-x86_64.tar.gz
cd Pacman42-Linux
./run.sh
```

The build definition is [pacman.spec](pacman.spec); the repeatable entry point
is [build_release.sh](build_release.sh). The unpacked build is also available
in `dist/Pacman42-Linux/`. Keep the complete extracted directory together. Its
launcher passes the adjacent editable `config.json` to the executable. Python
and the runtime dependencies, including the unchanged maze package, are
bundled; the player does not need a Python installation. Score writes use user
data even if a relative score path is configured in a frozen build.

The verified build uses PyInstaller 6.22.3, CPython 3.12.3 and Linux x86_64
with glibc 2.39; its archive is approximately 18 MB. The target is Linux x86_64
with a graphical desktop and a compatible system loader/libc. PyInstaller
bundles are platform-specific: use a system with a
glibc version comparable to or newer than the build system, and rebuild on an
older target distribution for broader compatibility. This is not a Windows or
macOS build. Build processing is defined by the executable Python spec, as
described in the [PyInstaller spec documentation](https://pyinstaller.org/en/stable/spec-files.html).

**Platform publication remains a manual step.** No itch.io upload or verified
public project URL is claimed; authenticated publisher access was unavailable.
To finish publication without sharing credentials:

1. Sign in to your own itch.io creator account and create a downloadable game.
2. Upload `release/Pacman42-Linux-x86_64.tar.gz` and mark the upload for Linux.
3. Select **No payments** so all files are freely downloadable. See the
   [official pricing options](https://itch.io/docs/creators/pricing).
4. Set visibility to Public with **Unlisted in search & browse**. This removes
   search/browse discovery; a profile link can be removed in the profile editor.
   For access limited to approved reviewers, use Restricted and download keys
   instead. See [official access controls](https://itch.io/docs/creators/access-control).
5. Add the controls, Linux requirements and a truthful project description.
   Save, visit the actual shared page, download the archive and launch it.
6. Put the verified page URL and date into the project-management release
   record. Do not include the supplied subject PDF in the public game archive.

## Configuration

[config.json](config.json) contains all supported fields.
[config.comments.json](config.comments.json) is a runnable commented example.
Only lines whose first non-whitespace character is `#` are removed before JSON
parsing. A literal `#` inside a JSON string remains intact. Inline/trailing
comments and trailing commas are not supported. UTF-8 with or without a BOM
is accepted. Unknown keys are ignored.

| Key | Default | Accepted bounds / meaning |
| --- | --- | --- |
| `highscore_filename` | `@userdata/highscores.json` | Safe relative JSON path; path policy below |
| `levels` | Ten levels listed below | Array of 10–100 level objects after repair |
| `levels[].width` | Matching default level | Integer 15–35 cells |
| `levels[].height` | Matching default level | Integer 15–35 cells |
| `levels[].level_max_time` | Global `level_max_time` | Optional override, 10–3600 seconds |
| `lives` | `3` | Integer 1–99 |
| `pacgum` | `42` | Integer 0–2000; requested minimum ordinary pellet count |
| `points_per_pacgum` | `10` | Integer 0–1,000,000 |
| `points_per_super_pacgum` | `50` | Integer 0–1,000,000 |
| `points_per_ghost` | `200` | Integer 0–1,000,000 |
| `seed` | `42` | Integer 1–2,147,483,647; first level only |
| `level_max_time` | `180` | Number 10–3600 seconds |
| `power_duration` | `8` | Number 1–60 seconds |
| `ghost_respawn_delay` | `7` | Number 5–10 seconds |
| `player_speed` | `5` | Number 1–15 cells per second |
| `ghost_speed` | `1.5` | Number 0.5–12 base cells per second |
| `pellet_coverage` | `0.8` | Number 0.65–1.0 of eligible cells |

Change `ghost_speed` in the selected configuration file to tune the base
speed. A valid file value takes precedence over the code's fallback.
`DEFAULT_GHOST_SPEED` in `pacman/configuration.py` supplies both the
`GameConfig` default and the parser fallback when this field is missing or
has an invalid type. The bounds 0.5 and 12 are validation limits, not extra
movement speeds. Later-level and frightened-state multipliers still apply.

Default dimensions by level are `19x17, 19x17, 21x17, 21x19, 21x19,
23x19, 23x21, 25x21, 25x23, 27x23`. Even dimensions are supported. Level timer
overrides are optional; omitted overrides inherit the loaded global limit.
The shipped configurations set later-level overrides for practical pacing:
their ten countdowns are **180, 180, 210, 240, 240, 270, 300, 330, 360, 400
seconds**. The parser's global fallback is 180 seconds. These limits were
doubled for a more forgiving run; the subject requires a time limit but gives
90 seconds only as an example (section 6.7). Remove an override to inherit the
global setting. [pacing_check.json](project_management/pacing_check.json)
retains the actual traversal evidence for the earlier, shorter time profile;
it is not presented as a new traversal of the current settings.

Numeric fields reject booleans, numeric strings and non-finite values. Integer
fields also reject fractional/float JSON values. Missing or wrong-type values
use defaults and emit warnings; finite out-of-range values are clamped and
warned. A missing, short or invalid level array is repaired/padded to at least
ten. Bad entries use the corresponding default dimensions and the global time;
entries beyond the tenth use the tenth default for repairs. More than 100
entries are truncated with a warning. Invalid score filenames recover to the
user-data default. Whole-file read/JSON/root failures follow the clean exit
policy in Instructions.

The PDF does not define `pacgum` as a count or density. Here it means a
**requested minimum ordinary pellet count**. Let `eligible` be reachable cells
excluding the player start, four ghost starts and four power-pellet cells:

```text
ordinary count = min(eligible, max(pacgum, ceil(eligible * pellet_coverage)))
```

The 80% default and 65% lower coverage bound are implementation choices to keep
pellets in most usable corridors. Reserved starts and blocked `42` cells are
never filled. Edit configuration and restart the program to apply changes;
there is no hidden hardcoded substitute for accepted settings.

## Highscore

JSON keeps the ten local records inspectable without a database. Atomic file
replacement protects the previous save if a write fails.

`HighScoreStore` loads at application start and saves after every confirmed
completed run. The file contains a JSON array:

```json
[
  {"name": "PLAYER42", "score": 1250},
  {"name": "ADA", "score": 700}
]
```

Only ten non-negative integer scores are retained, highest first. Ties preserve
older entry order. Names contain at most ten printable ASCII letters, digits
or spaces; blank names and punctuation are rejected with feedback. Leading
and trailing spaces are removed when stored. The end screen offers `PLAYER`
as an explicit Esc action. Zero scores and repeated player names are valid.

The default resolves to `$XDG_DATA_HOME/forty-two-pacman/highscores.json`, or
`~/.local/share/forty-two-pacman/highscores.json` when XDG_DATA_HOME is absent or
relative. `@userdata/subfolder/name.json` explicitly uses that data directory.
Safe relative filenames such as `scores/top.json` resolve beside the selected
configuration in a source run. Frozen builds redirect those paths under user
data so install assets can remain read-only.

Paths must end in `.json`, be at most 240 characters, and use portable
non-hidden components beginning with an ASCII letter, digit or underscore;
following characters may additionally be dots, dashes and spaces. Absolute
paths, `..`, `.`, backslashes, colons, repeated separators, symlink escapes and
protected system destinations are rejected. Direct configuration fields are
repaired with warnings before startup proceeds.

Missing files mean an empty leaderboard. Invalid records are skipped; broken
JSON, wrong root data, invalid encoding and read errors produce warnings while
preserving an existing valid in-memory table. Saving writes a temporary file
in the destination directory, flushes and syncs it, then replaces the old file
atomically. Failed writes retain the old file and in-memory score; the main
menu shows a storage warning. A later successful save persists the current
table. A corrupt file is not silently treated as valid data; a confirmed later
save can replace it with the recovered table. Concurrent application writers
are not merged; the last completed atomic save wins.

A score destination resolving to the active configuration is also rejected;
the parser warns and selects user data so score saving cannot overwrite it.

## Maze Generation

The assigned artifacts are `mazegenerator-00001(1).zip` and its original
`mazegenerator-2.1.0-py3-none-any.whl`. The wheel copied into `vendor/` is
byte-for-byte identical. Original artifact SHA-256 values are recorded in
[artifact_hashes.json](project_management/artifact_hashes.json). No generator
source, installation metadata or algorithm is modified or monkey-patched.
The final integrity check also compares installed source/metadata and validates
its wheel RECORD. Re-run it with
`.venv/bin/python tools/verify_integrity.py`.

The adapter uses the installed public export and verified constructor:

```python
from mazegenerator import MazeGenerator

generator = MazeGenerator(
    size=(width, height),
    perfect=False,
    entry_cell=(0, 0),
    exit_cell=(width - 1, height - 1),
    seed=seed,
)
walls = generator.maze
```

The package README's `MazeGenerator(width=..., height=...)` example is wrong
for this wheel; it raises `TypeError`. Coordinates are `(x, y)` and the grid is
`walls[y][x]`, height rows by width columns. Each cell is an integer bitmask:
North `1`, East `2`, South `4`, West `8`. A set bit means a blocked side. The
adapter checks grid shape, mask types, outer boundaries and reciprocal walls
before copying the result into immutable tuples and a read-only adjacency map.
Movement requires an open side and the reciprocal open side of its destination.

Mask `15` is a four-walled isolated cell, including the generator's protected
central `42` pattern. These cells are drawn as obstacles and excluded from the
largest connected gameplay component. The preferred center start is used when
reachable; otherwise the nearest reachable tile to the geometric center is
chosen deterministically. This handles legal even sizes such as `20x20`, whose
exact center can be blocked.

Four ghosts reserve distinct reachable corner positions first, taking actual
corners when available. Four power pellets take the closest remaining valid
positions to their respective corners, avoiding all entity starts. This
explicit corner-region policy resolves the requirement to put both objects
in each corner without overlapping a dangerous ghost and a power pellet.

The first level uses the positive configured seed, default 42. Later levels
pass `seed=0`, which requests fresh randomness in this wheel. Every generation
uses `perfect=False` to permit loops. The generator changes module-global
random state; AI and item placement use independent `random.Random` instances.
Generation failure, a missing dependency or an invalid maze yields a visible
error screen and a route back to the menu. There is no replacement generator.

## Implementation

`Maze` interprets the generator's existing topology; breadth-first search with
`collections.deque` finds connected components and shortest-path distances.
Ghosts minimize distance to chase and maximize distance to flee. Tied routes
use the game's private RNG, preferring forward motion among equally good
choices. All four ghosts use this policy and have distinct displayed colors.
Their movement speed increases 3.5% per later level, capped at a 1.35 multiplier;
frightened ghosts move at 70% of their current speed.

`Actor` stores a cell, optional neighboring target and fractional progress.
The player buffers desired turns and can reverse along the current open edge.
Both actor types spend their movement budget on validated graph edges. A
120 Hz fixed-step simulation updates movement, countdowns, collectible sets
and continuous-position contacts independently of rendering. The graphical
loop targets 60 frames per second and caps a single observed frame gap at
0.25 seconds. Consuming an item removes it before rewarding points; an eaten
ghost becomes inactive before another contact can reward it. This keeps scores
monotonic and prevents repeated life losses or rewards from one frame.

### Graphics and MLX equivalence

All pygame calls used for the playable frontend are centralized in
[graphics.py](pacman/graphics.py). The game uses window/image/pixel/text/event
operations supported by MLX. The adapter does its own Bresenham lines, filled
circle/ellipse/polygon scanlines, color gradients and character rasterization; it does not use pygame's shape,
transform, sprite, mixer, shader or physics facilities.

| Adapter operation | pygame calls | Equivalent MLX capability |
| --- | --- | --- |
| Open/title/close | `display.init`, `set_mode`, `set_caption`, `quit` | `mlx_init`, `mlx_new_window` with title, `mlx_destroy_window` |
| Desktop fit | `display.Info`; application coordinate/radius/font scaling | `mlx_get_screen_size`; application pixel-coordinate scaling |
| Image allocation | `Surface` | `mlx_new_image` |
| Pixel/color runs | `Surface.set_at`, `Surface.fill` | Write image memory from `mlx_get_data_addr`, or `mlx_pixel_put` |
| Image copy/frame | `Surface.blit`, `display.flip` | Copy image pixels; `mlx_put_image_to_window` |
| Garden shapes/gradients | Own scanlines through `Surface.fill` | Application-written pixels in MLX image memory |
| Cached scenery | Offscreen `Surface`, `blit` | Reuse an allocated MLX image |
| Text placement | `font.Font`, `Font.render`, `blit` | `mlx_string_put`, or glyph pixels in an MLX image |
| Keyboard/text/close | `event.get`, key names, text-input events | `mlx_key_hook` / `mlx_hook` and key-to-character mapping |
| Main loop/pacing | `time.Clock.tick` plus event/update loop | `mlx_loop_hook` / `mlx_loop` with a standard clock |
| Cleanup/status | Font/cache release, display state query | Release images/window and track owned resources |

Font rendering is used only to place readable strings; scalable glyphs can be
rasterized into the same MLX pixel buffers. Alpha sprites can likewise be
copied pixel by pixel over the frame. This is an operation-level portability
mapping, not a claim that pygame and MLX have identical APIs. See
[MLX prototypes](https://harm-smits.github.io/42docs/libs/minilibx/prototypes.html),
[pygame display](https://www.pygame.org/docs/ref/display.html) and
[pygame font](https://www.pygame.org/docs/ref/font.html).

The main menu uses a separate monotonic animation clock. Its static garden is
cached once; only foliage, clouds, fireflies, flowers and water are redrawn.
Decorative variation uses a private random source, leaving maze/AI randomness
and all gameplay timers untouched. New captures and measurements are recorded
in [the garden update](project_management/menu_garden_update.md).

The optional developer screenshot function saves a rendered buffer to PNG for
test evidence; gameplay and the normal event loop do not rely on image export.
Actual diagnostic captures are retained in
[project_management/screenshots/](project_management/screenshots/). They are
rendered application evidence, not claimed screenshots of a human playthrough.

## General Software Architecture

| Module / artifact | Responsibility and main objects |
| --- | --- |
| `pac-man.py` | Exact CLI, startup boundaries, score/config loading |
| `pacman/configuration.py` | Immutable `GameConfig` / `LevelConfig`, repairs, safe paths |
| `pacman/maze_adapter.py` | `Maze`, `Direction`, validation and BFS topology |
| `pacman/models.py` | `Game`, `Actor`, `Ghost`, `State`, timers and rules |
| `pacman/ghost_ai.py` | Chase/flee neighbor selection |
| `pacman/cheats.py` | Resettable review-mode flags |
| `pacman/highscores.py` | `ScoreEntry`, `HighScoreStore`, validation/atomic persistence |
| `pacman/error_logging.py` | `ErrorLogSession`, rotating UTC diagnostics and console fallback |
| `pacman/app.py` | `App`, menus, state routing and name entry |
| `pacman/graphics.py` | `Graphics`, `InputEvent`, resource ownership |
| `pacman/menu_background.py` | `GardenBackground`, cached scenery and independent decorative animation |
| `pacman/finish_background.py` | `FinishBackground`, distinct animated victory/loss gardens |
| `pacman/rendering.py` | `Renderer`, visual presentation from model state |
| `pacman/smoke.py` | Opt-in integrated application diagnostic |
| `dev_tests/` | Developer-only unit and integration checks |
| `pacman.spec`, `build_release.sh` | Reproducible standalone packaging |

Data flows from configuration into the model and score store, from the assigned
generator into immutable maze topology, and from normalized input into `App`
and `Game`. The model updates independently of display calls. The renderer
reads state and draws through `Graphics`; the application records a result
once and returns to its menu. Expected dependency, file and generation failures
are caught at the boundary that can explain or recover from them.

The model states are Menu, Playing, Paused, Transition, Game Over and Victory.
The application additionally routes main-menu, instructions, highscores and
error pages. A 1.5-second level-cleared transition carries score/lives to a
freshly generated level. Keeping these responsibilities separate makes defense
changes local: points/bounds in configuration, AI choices in `ghost_ai.py`,
rules in `models.py`, menu behavior in `app.py`, appearance in `rendering.py`.

## Project Management

Pac-Man 42 is a team project by **mal-jama** and **mewaysi**. Current study,
testing and defense responsibilities follow
[PACMAN_TEAM_PARTS.md](PACMAN_TEAM_PARTS.md):

| Member | Assigned part | Main responsibilities |
| --- | --- | --- |
| **mewaysi** | **Part 1 — Game Engine, Maze, Player, Ghost AI & Gameplay** | Maze integration/topology, movement, collisions, ghosts, collectibles, powers, scoring, timers, levels and cheats |
| **mal-jama** | **Part 2 — UI, Application, Configuration, Highscores & Release** | CLI/startup, application loop, keyboard events, menus/rendering, animated garden, configuration, score persistence, packaging and documentation |

Both members review the application/model boundary, end-to-end diagnostics,
subject requirements and project-management evidence. Each member should be
able to explain the whole game's purpose and demonstrate changes in their
assigned modules. The assignment describes current review responsibilities;
it does not retroactively attribute individual files or implementation dates.

The [project-management directory](project_management/README.md) contains the
plan, recorded progress, decisions, risks, acceptance checks, fixes and release
actions. Records retain the actual dates of implementation checks and the
later garden-menu update. Test and release evidence is linked from
[acceptance_tests.md](project_management/acceptance_tests.md); original supplied
artifact checksums are recorded separately. Native desktop peer review and a
verified free unlisted/private platform upload remain release actions until
the team records their actual completion.

## Resources

- The supplied [en.subject-3.pdf](../en.subject-3.pdf), Pacman version 1.5, is
  the local assignment authority. It is retained unchanged beside the project
  folder and excluded from the game distribution.
- The supplied original `mazegenerator` 2.1.0 wheel and installed metadata are
  the authority for its actual constructor, wall masks and package metadata.
- [Python JSON](https://docs.python.org/3/library/json.html) documents the parser
  used for configuration and leaderboard persistence.
- [Python random](https://docs.python.org/3/library/random.html) describes
  independent `Random` instances used to isolate gameplay from generator seeds.
- [Python deque](https://docs.python.org/3/library/collections.html#collections.deque)
  supports the BFS queues used for topology and distance calculations.
- [pygame display](https://www.pygame.org/docs/ref/display.html),
  [pygame font](https://www.pygame.org/docs/ref/font.html) and
  [MiniLibX reference](https://harm-smits.github.io/42docs/libs/minilibx)
  informed the graphics adapter and equivalence mapping.
- [PyInstaller specs](https://pyinstaller.org/en/stable/spec-files.html)
  informed repeatable packaging.
- [itch.io access control](https://itch.io/docs/creators/access-control) and
  [pricing](https://itch.io/docs/creators/pricing) support the manual unlisted,
  free publication procedure.
