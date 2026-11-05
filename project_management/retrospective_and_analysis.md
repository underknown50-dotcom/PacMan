# 🔍 Project Analysis, Technical Choices & Retrospective

> **Project:** 42 Pac-Man  
> **Course:** 42 Curriculum (Python 3.10+, Team of 2)  
> **Documentation:** Required by Chapter 8 (Project Management)

---

## 1. Project Analysis & Architectural Choices

During initial system design, we analyzed several approaches for engine, architecture, and logic to satisfy both the 42 subject requirements and strict engineering quality standards.

### 1.1 Graphics & Window Engine: Pygame Community Edition (`pygame-ce`)
- **Analysis:** The 42 subject permits modern graphical toolkits or MiniLibX-style raster primitives. We compared Tkinter, raw Pygame, ModernGL, and `pygame-ce`.
- **Decision:** We selected `pygame-ce` (version 2.5+).
- **Rationale:**
  - Active open-source development, built-in SDL2 backend with hardware-accelerated rendering.
  - Native support for modern Python 3.12+ type stubs, critical for passing `mypy . --strict`.
  - Fast primitive drawing (`pygame.draw.circle`, `pygame.draw.line`, `pygame.draw.rect`) allowing pure procedural rendering without requiring external asset files.

### 1.2 Maze Integration: Adapter Design Pattern
- **Analysis:** Chapter 4 strictly requires integrating an external precompiled wheel (`mazegenerator-2.1.0-py3-none-any.whl`) without modifying the wheel package itself.
- **Decision:** Implemented `pacman.adapter.MazeAdapter`.
- **Rationale:**
  - Isolates third-party API quirks from our core game engine.
  - Converts external cell data structures directly into an internal 2D bitmask grid matrix `List[List[int]]`.
  - Integrates fallback procedural maze generation if the external library throws an unexpected error or fails to load.

### 1.3 Collision & Movement: Bitwise Bitmask Navigation
- **Analysis:** The external generator represents cell walls as bitmasks: `1 = North`, `2 = East`, `4 = South`, `8 = West`, and `15 = Solid center block`.
- **Decision:** Implemented corridor check using bitwise operators:
  ```python
  def is_wall_between(current_tile, next_tile, direction):
      # Current cell has wall in direction OR neighbor cell has opposing wall
      return (current_tile & dir_bit) != 0 or (next_tile & opp_bit) != 0
  ```
- **Rationale:**
  - Exact $O(1)$ constant-time lookup for movement decisions.
  - Guarantees zero wall-clipping for both Pac-Man and ghosts.

### 1.4 Central State Machine (`GameState`)
- **Analysis:** Pac-Man requires multiple discrete screens (Main Menu, Active Game, Paused, Level Clear, Game Over, Victory, Highscores, Instructions).
- **Decision:** Implemented a centralized finite state machine in `pacman.game.Game`.
- **Rationale:**
  - Completely separates update logic, event handling, and rendering.
  - Prevents race conditions and unintended input leakage between screens.

---

## 2. Summary of Blocking Points & How They Were Resolved

| # | Blocking Point / Conflict | Root Cause | Resolution Strategy |
|:---:|---|---|---|
| **1** | **Solid "42" Logo in Center** | The external generator places a solid `15` block containing the 42 logo in the center of odd-dimension mazes. Defaulting Pac-Man's spawn to `(width // 2, height // 2)` placed Pac-Man inside a solid wall. | Designed `find_safe_center(grid, w, h)`: uses a Breadth-First Search (BFS) flood-fill starting at the center coordinate to find the nearest open corridor tile with maximum adjacent exits. |
| **2** | **CLI Constraint vs. Packaged Build** | Chapter 5.1 mandates `python3 pac-man.py <config.json>` (exactly one argument). However, Chapter 7 requires a packaged application for Itch.io that users can double-click without terminal flags. | In `validate_args()`, checked `getattr(sys, 'frozen', False)`. If running as a frozen executable without CLI arguments, it seamlessly loads the bundled `config.json`. If executed as a script, it strictly enforces the single-argument CLI rule. |
| **3** | **JSON Standard Comments Rejection** | Evaluators or players may write human comments (`#`, `//`, `/* */`) in `config.json`. Standard Python `json.load()` crashes with a `JSONDecodeError`. | Built a custom pre-parser scanner in `ConfigLoader` that removes single-line comments (`#` and `//`) and multi-line comments (`/* ... */`) while respecting quoted string literals. |
| **4** | **Packaging Spec File Tracking** | PyInstaller build creates `pac-man.spec`. Running `make clean` previously wiped all `*.spec` files, deleting the mandatory repository root spec file. | Updated `Makefile` clean rule to preserve `pac-man.spec`, updated `.gitignore` with `!pac-man.spec`, and committed `pac-man.spec` directly at repository root. |

---

## 3. Team Dynamics & Retrospective

- **Pair Programming Efficiency:** Alternating driver/navigator roles for critical subsystems (e.g. Ghost AI algorithms and bitmask collision) cut debugging time in half and eliminated wall-clipping bugs before committing.
- **Strict Typing as Quality Assurance:** Adopting `mypy --strict` from Day 1 caught several potential `NoneType` attribute errors during state transitions and ghost respawn delays.
- **Defense Preparedness:** By engineering comprehensive cheat hotkeys (`I`, `L`, `F`, `+`, `S`), both teammates can fluently demonstrate all game states and levels to evaluators without hesitation.
