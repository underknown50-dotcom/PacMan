# Technical Decisions and Risk Management

## 1. Key Technical Decisions

| Decision | Why We Chose It |
| --- | --- |
| **Strict MVC Architecture** | Keeps `models.py` 100% free of Pygame/graphics so physics are deterministic and testable headless (`make smoke`). |
| **Single Pygame Facade (`graphics.py`)** | Enforces the Chapter 4 MLX-similarity rule by locking all `import pygame` calls into one file and rasterizing lines, circles, and polygons in our own pixel code. |
| **Unmodified `mazegenerator` Wheel** | Preserves the Chapter 5.4 contract so reinstalling the wheel from the intranet during defense works identically. |
| **120 Hz Fixed Physics Step (`STEP = 1/120`)** | Keeps Pac-Man and ghost speeds identical on slow laptops and high-refresh monitors, with `dt` clamped at `0.25s` to protect against lag spikes. |
| **4 Authentic Arcade Ghost Personalities** | Implements Blinky (chase), Pinky (4 tiles ahead), Inky (Blinky reflection), and Clyde (shy within 8 tiles) using BFS shortest-path distances. |
| **Atomic Highscore Saves** | Writes to a temporary file + `flush()` + `os.fsync()` + `os.replace()` inside `~/.local/share/forty-two-pacman/` so crashes or read-only installs never corrupt scores. |
| **PyInstaller Linux Bundle (`make release`)** | Produces a self-contained `Pacman42-Linux` folder and `.tar.gz` archive runnable via `./run.sh` without Python installed. |

## 2. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| **Broken or hostile `config.json` crashes the app** | Strip `#` comments, lowercase all keys, reject `bool` for numeric fields, clamp out-of-range values with defaults, and exit cleanly without tracebacks on unreadable JSON. |
| **Maze center lands on a sealed `"42"` wall cell** | Select the nearest reachable cell inside `_largest_component()` without altering any maze walls. |
| **External generator resets Python's global `random`** | Give ghost AI and pellet placement their own private `random.Random()` instances. |
| **Window too large for small laptop screens** | Query desktop resolution at startup and scale logical 1000×850 coordinates down smoothly (minimum 640×544). |
| **Pausing leaves hidden timers running** | Freeze the entire model `update()` while paused so countdown, power, boost, and respawn timers all stop together. |
| **Local archive mistaken for platform deployment** | Publish the tested `Pacman42-Linux-x86_64.tar.gz` build as a free unlisted/private download on itch.io before defense. |
