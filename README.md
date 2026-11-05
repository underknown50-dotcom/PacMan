*This activity has been created as part of the 42 curriculum by hamoody, teammate2.*

# 42 Pac-Man: Ghosts! More Ghosts!

A complete, robust, type-safe recreation of the classic 1980 Namco arcade hit **Pac-Man** written in modern Python 3.10+ using object-oriented architecture, primitive raster graphics conforming to MiniLibX standards, and integration with an external procedural maze generator.

---

## 📖 Description

The objective of this project is to recreate the authentic gameplay, entity dynamics, and ghost artificial intelligence of **Pac-Man**. The player controls Pac-Man through a procedurally generated maze, eating pacgums and super-pacgums while evading four distinct ghosts (Blinky, Pinky, Inky, and Clyde). 

Key features include:
- **Campaign Progression**: 10 progressive levels with escalating grid dimensions and countdown timers.
- **Authentic Ghost AI**: Distinct pursuit algorithms for each ghost (direct chasing, ambush targeting, flanking pinch maneuvers, and proximity cowardice).
- **Commented JSON Configuration**: Full support for `#` and `//` comments with resilient fallback handling against missing or corrupted keys.
- **Persistent Highscores**: Disk storage retaining the Top 10 scores with validated player handles.
- **Peer-Review Cheat Suite**: Instant review shortcuts including Invincibility, Level Skip, Ghost Freezing, and Speed Boosts.
- **Zero-Traceback Guarantee**: Strict exception trapping preventing any uncaught Python tracebacks during defense.

---

## 🚀 Instructions

### 1. Requirements & Installation
Ensure you have Python 3.10+ and `make` installed.

To install dependencies using the project Makefile:
```bash
make install
```
This installs `pygame-ce`, `flake8`, `mypy`, and the local `mazegenerator` wheel located in `wheels/`.

### 2. Execution
Run the game using the Makefile or directly via Python with exactly one configuration argument:
```bash
make run
# or
python3 pac-man.py config.json
```

### 3. Debugging
Run in interactive debug mode using Python's built-in `pdb`:
```bash
make debug
```

### 4. Code Standards & Linting
Verify static type hints and PEP 8 formatting:
```bash
make lint
# Or strict verification:
make lint-strict
```

### 5. Automated Tests
Run the comprehensive unit test suite:
```bash
make test
```

### 6. Packaging for Distribution (Chapter 7)
Generate a standalone release build for distribution on Itch.io:
```bash
make package
```
The packaged binary, configuration, and in-package instructions will be built in `dist/pac-man/`.

---

## 🎮 Controls & Gameplay

| Key | Action |
|---|---|
| **Arrow Keys / WASD** | Move Pac-Man through corridors |
| **P** | Pause / Resume game |
| **ESC** | Pause game or Return to Main Menu |
| **Enter / Space** | Confirm menu selections / Submit highscore |

### Peer-Review Cheat Hotkeys (Chapter 6.5)
- **`I`**: Toggle **Invincibility** (Pac-Man cannot lose lives)
- **`L`**: **Level Skip** (Instantly completes the current level)
- **`F`**: **Ghost Freeze** (Stops all ghost movement)
- **`+` / `=`**: **Extra Life** (Adds 1 life)
- **`S`**: **Speed Boost** (Increases Pac-Man's movement speed by 60%)

---

## ⚙️ Configuration

The game accepts a custom configuration file in JSON format with full comment support (`#` lines are ignored).

### Structure & Default Values
```json
# Default configuration for 42 Pac-Man
{
    # Highscore file location
    "highscore_filename": "highscores.json",

    # Starting player lives [1 - 99]
    "lives": 3,

    # Scoring parameters
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,

    # Time limit per level in seconds [10 - 600]
    "level_max_time": 90,

    # Fixed seed for Level 1 determinism
    "seed": 42,

    # Level array (minimum 10 levels)
    "levels": [
        {"level": 1, "width": 15, "height": 15, "max_time": 90},
        {"level": 2, "width": 15, "height": 15, "max_time": 90},
        ...
    ]
}
```

### Fault-Tolerant Handling (Chapter 5.3)
If `config.json` contains invalid numbers, missing keys, or out-of-range bounds, `ConfigLoader` logs an informative warning to `stdout`, clamps the value to safe operational ranges, and continues execution without crashing. Unknown keys are safely ignored.

---

## 🏆 Highscore System

The persistent highscore system records the **Top 10** scores in a local JSON file (`highscores.json`).

### Why this design?
1. **Human-Readable & Portable**: JSON ensures transparent inspection by evaluators and players.
2. **Defensive I/O**: File access is guarded by `try...except` context managers. Missing files, corrupt syntax, or invalid JSON structures are automatically caught, logging a warning and falling back to a clean in-memory score table.
3. **Strict Validation**: In accordance with Chapter 5.5, player names are sanitized to a maximum of 10 alphanumeric characters and spaces (`^[a-zA-Z0-9 ]{1,10}$`). Scores must be non-negative integers.
4. **Seamless Flow**: Highscores load automatically at launch, update when completing or ending a game, and persist to disk on exit.

---

## 🌀 Maze Generation Integration

The game does not generate its own mazes; it interfaces with the assigned `mazegenerator` wheel package located in `wheels/`.

### How the Adapter Works (`pacman/adapter.py`)
1. **Zero Package Modification**: The assigned package is consumed strictly through its public API as required by Chapter 5.4.
2. **Pac-Man Corridor Loops (`perfect=False`)**: The adapter explicitly instantiates `MazeGenerator(size=(w, h), perfect=False, seed=seed)`. Setting `perfect=False` induces loops and eliminates dead-ends so Pac-Man cannot be trapped.
3. **Bitmask Translation**: The external package encodes walls using bitmasks:
   - `1`: North wall
   - `2`: East wall
   - `4`: South wall
   - `8`: West wall
   - `15`: Solid impenetrable block (used by the package to draw the center '42' logo).
4. **Safe Spawn Resolution**: The adapter uses breadth-first search (BFS) to locate the nearest walkable corridor cell to the center `(w // 2, h // 2)` and the four corners, ensuring entities never spawn inside solid blocks.
5. **Fallback Safety**: If the external package fails or raises an error, `MazeAdapter` catches the exception and constructs a safe bordered corridor grid.

---

## 🏗️ General Software Architecture

The project follows a decoupled, modular Model-View-Controller (MVC) architecture with clear separation of concerns across logic, rendering, and data translation:

```
                      ┌────────────────────────┐
                      │       pac-man.py       │ (Entry Point & Event Loop)
                      └───────────┬────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
 ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
 │ pacman/config.py   │ │   pacman/game.py   │ │ pacman/renderer.py │
 │ (Comment Stripper  │ │ (State Machine,    │ │ (Arcade Primitives,│
 │  & Clamping)       │ │  Rules, Collisions)│ │  HUD, Screens)     │
 └────────────────────┘ └─────────┬──────────┘ └────────────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            ▼                     ▼                     ▼
 ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
 │ pacman/models.py   │ │ pacman/adapter.py  │ │pacman/highscores.py│
 │ (Player & Ghost AI │ │ (External Maze     │ │ (Top 10 Persistence│
 │  Targeting Engine) │ │  Bitmask Adapter)  │ │  & Sanitization)   │
 └────────────────────┘ └────────────────────┘ └────────────────────┘
```

### Module & Class Relationships
- **`pacman/models.py`**:
  - `Direction`: Enumeration of 2D direction vectors (`UP`, `DOWN`, `LEFT`, `RIGHT`) providing coordinate deltas and opposite direction computation.
  - `Player`: Encapsulates Pac-Man state, speed, continuous corridor motion, input buffering, and cheat invincibility.
  - `Ghost`: Autonomous agent encapsulating personality targeting, FSM modes (`CHASE`, `FRIGHTENED`, `EATEN`), and tile-based Euclidean routing.
- **`pacman/adapter.py`**:
  - `MazeAdapter`: Wraps `MazeGenerator` from `mazegenerator-2.1.0-py3-none-any.whl`, exposing `can_move()`, BFS corridor discovery, and fallback procedural maps.
- **`pacman/game.py`**:
  - `Game`: Core controller managing transitions between `GameState` values (`MENU`, `PLAYING`, `PAUSED`, `GAME_OVER`, `VICTORY`, `HIGHSCORES`, `INSTRUCTIONS`), consumable tracking, score, lives, level timers, and cheat key toggles.
- **`pacman/renderer.py`**:
  - `Renderer`: MLX-style rasterizer drawing geometric shapes (`pygame.draw.line`, `pygame.draw.circle`, `pygame.draw.rect`) and rendering text HUD surfaces without external image sprites.
- **`pacman/highscores.py`**:
  - `HighscoreManager`: Handles persistent disk I/O, regex name sanitization, descending sort, and corrupted file recovery.
- **`pacman/config.py`**:
  - `ConfigLoader`: Defensive JSON parser with comment removal (`#`, `//`, `/* */`), case-insensitive key normalization, and value clamping.

---

## 💻 Implementation

### Technical Summary & Core Mechanics
1. **Delta-Time & Frame Independence**:
   - The game loop runs at 60 FPS utilizing `pygame.time.Clock.tick(60)`. Movement speeds (expressed in pixels per second) are scaled by elapsed time $\Delta t$ to guarantee identical movement speeds across different machines.
2. **Bitwise Corridor Traversal**:
   - Corridors are governed by bitmask wall encoding: `1=North`, `2=East`, `4=South`, `8=West`, and `15=Solid 42 block`.
   - Motion between tile $(x, y)$ and $(x+dx, y+dy)$ checks both current wall bits and the neighbor's opposing bit in $O(1)$ constant time, preventing wall clipping.
3. **Turn Buffering (Cornering)**:
   - Pac-Man queues user directional inputs. If the player presses a turn key before an intersection, the turn executes the exact moment the perpendicular corridor becomes walkable.
4. **Finite State Machine (FSM)**:
   - Ghost states (`CHASE`, `FRIGHTENED`, `EATEN`) transition based on game events (eating super-pacgums, timers, reaching home spawn).
5. **Zero Traceback Defensive Guarantee**:
   - Every file interaction, command-line parameter, and runtime event is enclosed in guarded exception blocks, logging helpful diagnostic alerts to `stdout` rather than crashing.

---

## 🧠 Ghost Artificial Intelligence Explained

Each ghost possesses an autonomous personality mirroring the 1980 arcade design:

1. **Blinky (Red) - Direct Chaser**:
   - *Target*: Directly on Pac-Man's current grid tile `(px, py)`.
   - *Behavior*: Aggressive and relentless pursuer.
2. **Pinky (Pink) - Ambush Predictor**:
   - *Target*: 4 tiles ahead of Pac-Man's current facing direction `(px + 4*pdx, py + 4*pdy)`.
   - *Behavior*: Cuts off escape routes and corners the player.
3. **Inky (Cyan) - Flanker Pinch**:
   - *Target*: Vector reflection between Blinky and an offset tile 2 steps ahead of Pac-Man.
   - *Behavior*: Pinches the player in tandem with Blinky.
4. **Clyde (Orange) - Cowardly Distance-Based**:
   - *Target*: If Euclidean distance to Pac-Man $> 8$ tiles, targets Pac-Man. When closer than 8 tiles, retreats to his home corner in the bottom-left.
   - *Behavior*: Alternates between stalking and fleeing.
5. **Frightened Mode**:
   - Triggered when Pac-Man eats a super-pacgum. Ghosts turn dark blue, reverse direction, move at reduced speed, and make pseudo-random turn decisions at intersections.
6. **Eaten Mode**:
   - Only eyes remain; moves at high speed back to the spawn corner to regenerate.

---

## 📁 Project Management (Chapter 8)

Full project management artifacts and evidence are organized in the [`project_management/`](file:///c:/Users/7moody/Desktop/pac-man/project_management) directory:
- [**`daily_plan.md`**](file:///c:/Users/7moody/Desktop/pac-man/project_management/daily_plan.md): 14-day sprint roadmap with task distribution and acceptance criteria.
- [**`team_organization.md`**](file:///c:/Users/7moody/Desktop/pac-man/project_management/team_organization.md): Role allocation, decision protocols, and Git workflows.
- [**`risk_analysis.md`**](file:///c:/Users/7moody/Desktop/pac-man/project_management/risk_analysis.md): Technical risks (config crashes, typing errors, packaging) and mitigations.
- [**`test_plan.md`**](file:///c:/Users/7moody/Desktop/pac-man/project_management/test_plan.md): Acceptance test matrix, bug resolution log, and edge case verifications.
- [**`retrospective_and_analysis.md`**](file:///c:/Users/7moody/Desktop/pac-man/project_management/retrospective_and_analysis.md): Architectural analysis, engineering decisions, and blocking points log.

---

## 📚 Resources & AI Usage

### References
- *The Pac-Man Dossier* by Jamey Pittman (In-depth analysis of original ghost algorithms and tile logic).
- Python 3.12 `typing` and `mypy` documentation for static type enforcement.
- Pygame-CE (Community Edition) documentation for 60 FPS surface management.

### AI Tool Usage Disclosure (Chapter 9 Requirement)
In compliance with the 42 AI policy:
- **Architecture & Design**: AI was utilized to analyze the subject constraints, draft the modular MVC interface contracts, and design the safe fallback mechanisms for the external wheel.
- **Bitmask Reverse-Engineering**: AI assisted in inspecting the byte structure and bitmask flags (`1, 2, 4, 8, 15`) of the assigned `mazegenerator` wheel.
- **Code Standards & Type Checking**: AI helped ensure strict type annotations across all classes and verify line lengths for `flake8` compliance.
- **Human Verification**: All code was tested, reviewed, and verified through unit tests and interactive test runs in Ubuntu WSL.
