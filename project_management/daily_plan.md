# 📅 Pac-Man Project: 14-Day Sprint & Daily To-Do Tracker

> **Project:** 42 Pac-Man (Team of 2)  
> **Duration:** 14 Days (Recommended 3–4 hours/day)  
> **Objective:** Deliver a complete, robust, type-safe Pac-Man game with custom level generator integration and deployment to Itch.io.

---

## 📊 Sprint Overview & Progress Matrix

| Day | Phase | Primary Objective | Status |
|:---:|:---|:---|:---:|
| **Day 1** | Foundation | Environment, Makefile, Wheel Inspection, Kanban setup | ✅ Done |
| **Day 2** | Adapter & Grid | Render static maze from external wheel | ✅ Done |
| **Day 3** | Player Movement | Pac-Man controls, corridor navigation & grid collision | ✅ Done |
| **Day 4** | Collectibles | Pacgums, Super-pacgums, and scoring logic | ✅ Done |
| **Day 5** | Persistence & Config | Fault-tolerant JSON parser (# comments) & Highscores | ✅ Done |
| **Day 6** | Ghost Basics | Ghost spawning, corridor movement, collision with player | ✅ Done |
| **Day 7** | Ghost AI & States | Chase logic, Frightened mode, Eaten/Respawn timer | ✅ Done |
| **Day 8** | Levels & Timer | 10+ levels progression, seeds (Level 1 fixed), time limits | ✅ Done |
| **Day 9** | UI & Game Screens | Main Menu, HUD, Pause, Game Over, Victory screen | ✅ Done |
| **Day 10** | Cheat Mode | Reviewer cheat hotkeys (Invincible, Skip, Freeze, etc.) | ✅ Done |
| **Day 11** | Robustness & Quality | Zero traceback defense test, flake8 & mypy strict pass | ✅ Done |
| **Day 12** | Project Management | Document timeline vs. actual, risk analysis, test plans | ✅ Done |
| **Day 13** | Packaging & Release | Standalone build (PyInstaller) & upload to Itch.io | ✅ Done |
| **Day 14** | README & Final Review | Complete README.md and mock peer-review defense | ✅ Done |

---


---

## 📈 Planned Schedule vs. Actual Timeline Tracking

| Phase / Milestones | Planned Window | Actual Completion | Variance & Observations |
|:---|:---:|:---:|---|
| **Phase 1: Foundation & Wheel Inspection (Days 1–2)** | Day 1–2 | Day 2 | **On track.** Discovered wheel bitmask encoding (1=N, 2=E, 4=S, 8=W, 15=Solid). |
| **Phase 2: Player Movement & Collectibles (Days 3–4)** | Day 3–4 | Day 4 | **On track.** Grid collision and buffered turns implemented cleanly. |
| **Phase 3: Config Loader & Highscores (Day 5)** | Day 5 | Day 5 | **On track.** Built custom comment-stripper (#, //, /* */) for JSON resilience. |
| **Phase 4: Ghost Behaviors & AI (Days 6–7)** | Day 6–7 | Day 7 | **On track.** Blinky, Pinky, Inky, and Clyde behaviors completed with Frightened/Eaten FSM. |
| **Phase 5: Level Progression & UI Screens (Days 8–9)** | Day 8–9 | Day 9 | **On track.** 10-level progression and all 6 screens (Menu, Play, Pause, GameOver, Victory, Highscore). |
| **Phase 6: Cheat System & Linting (Days 10–11)** | Day 10–11 | Day 11 | **On track.** make lint-strict passed with 0 errors across 13 files. |
| **Phase 7: Project Management & Packaging (Days 12–14)** | Day 12–14 | Day 14 | **Completed ahead of defense.** PyInstaller standalone build packaged and verified. |

## 🛠️ Daily Action Plans

---

### 🟢 Day 1: Foundation & Package Exploration
**Goal:** Have a clean working development environment, Makefile, and discover how the external maze wheel works.

- [x] **Teammate A (DevOps & Graphics Prep):**
  - [x] Initialize Git repository with a solid `.gitignore` (Python, virtual environment, OS files).
  - [x] Create `Makefile` with targets: `install`, `run`, `debug`, `clean`, `lint`.
  - [x] Install graphics dependency (`pygame-ce`).
  - [x] Test a minimal window that opens, displays black background, and exits cleanly on `ESC` or window close (`test_window.py`).
- [x] **Teammate B (Wheel Inspection & Research):**
  - [x] Unzip `mazegenerator-00001.zip` to obtain `mazegenerator-2.1.0-py3-none-any.whl`.
  - [x] Install the wheel into the virtual environment (`pip install wheels/...`).
  - [x] Write a scratch script `test_generator.py` to discover the API.
  - [x] Successfully generate a maze with `PERFECT=False` and print its dimensions/structure to console.
- [x] **Pair Work (Both):**
  - [x] Agree on Git branch workflow (`main`, `feature/graphics`, `feature/logic`).
  - [x] Document wheel findings: input arguments needed (`size=(width, height)`, `perfect=False`, `seed=42`) and bitmask return format (North=1, East=2, South=4, West=8, Solid=15).
- [x] **Day 1 Done Criteria:** `make install` dependencies established; scratch script successfully prints a generated maze; empty game window opens cleanly.

---

### 🟢 Day 2: The Maze Adapter & First Grid Rendering
**Goal:** Translate external maze data into your own grid and draw it on screen.

- [x] **Teammate A (Renderer):**
  - [x] Define tile size (e.g. $24 \times 24$ or $32 \times 32$ pixels).
  - [x] Implement `Renderer` class to draw blue wall tiles and empty corridor tiles on screen.
  - [x] Add basic camera / window sizing calculation based on maze dimensions.
- [x] **Teammate B (Adapter):**
  - [x] Implement `MazeAdapter` class that wraps the external package without modifying it.
  - [x] Convert whatever raw structure the wheel outputs into a clean internal 2D grid matrix `List[List[int]]`.
  - [x] Handle potential errors from the generator cleanly (catch exceptions and provide safe fallback).
- [x] **Pair Work (Both):**
  - [x] Connect `MazeAdapter` to `Renderer`: launch the game and see the generated maze drawn on screen!
- [x] **Day 2 Done Criteria:** Running `python3 pac-man.py` draws a complete generated maze on screen.

---

### 🟢 Day 3: Pac-Man Movement & Collision
**Goal:** Spawn Pac-Man in the center and allow smooth movement through corridors without walking through walls.

- [x] **Teammate A (Input & Animation):**
  - [x] Capture Arrow keys and WASD input in the event loop.
  - [x] Draw Pac-Man (yellow circle or sprite) with orientation (facing direction).
  - [x] Buffer input (so pressing Turn Right before an intersection queues the turn).
- [x] **Teammate B (Movement Physics & Collision):**
  - [x] Implement `Pacman` class (tracks grid coordinates `(x, y)`, direction `(dx, dy)`).
  - [x] Implement tile collision logic: check if the destination cell in the grid is a wall.
  - [x] Center spawn calculation: place player at `(width // 2, height // 2)`.
- [x] **Pair Work (Both):**
  - [x] Verify Pac-Man stops cleanly at walls and turns smoothly into corridors.
- [x] **Day 3 Done Criteria:** Player can steer Pac-Man around the entire maze without passing through walls.

---

### 🟢 Day 4: Collectibles (Pacgums, Super-pacgums, Score)
**Goal:** Populate corridors with pacgums, place super-pacgums in corners, and collect them.

- [x] **Teammate A (Visuals & Audio):**
  - [x] Render small white dots (pacgums) in corridors.
  - [x] Render larger pulsating dots (super-pacgums) in the 4 corners of the maze.
  - [x] Simple score counter display at the bottom or top of the screen.
- [x] **Teammate B (Game State Logic):**
  - [x] Populate grid with pacgums on empty corridor tiles.
  - [x] Locate the 4 accessible corner positions for super-pacgums.
  - [x] Implement eating logic: when player coordinate == dot coordinate, award points and remove dot.
  - [x] Level win condition: trigger level complete when all regular pacgums are eaten.
- [x] **Pair Work (Both):**
  - [x] Test that collecting every dot clears the maze and triggers a win event.
- [x] **Day 4 Done Criteria:** All corridors have pacgums, corners have super-pacgums, eating them awards points, and clearing dots detects level completion.

---

### 🟢 Day 5: Fault-Tolerant Config & Persistent Highscores
**Goal:** Build the comment-supporting config parser and the highscore JSON system.

- [x] **Teammate A (Config Parser):**
  - [x] Create `ConfigLoader`: reads JSON file but ignores lines starting with `#`.
  - [x] Implement safe defaults for every single key (`lives: 3`, `points_per_pacgum: 10`, `level_max_time: 90`, etc.).
  - [x] Defensive validation: if a key is missing, invalid type, or out of range, clamp to safe default, print warning, and **do not crash**.
  - [x] Unknown keys must be ignored without raising errors.
- [x] **Teammate B (Highscore System):**
  - [x] Create `HighscoreManager`: persistent storage in a JSON file.
  - [x] Validate player names: max 10 characters, alphanumeric and spaces only.
  - [x] Ensure scores are non-negative integers.
  - [x] Keep and sort top 10 scores; handle missing/corrupted highscore file gracefully.
- [x] **Pair Work (Both):**
  - [x] Write unit tests / scratch tests trying to break the config and highscore files with bad inputs.
- [x] **Day 5 Done Criteria:** Program loads game parameters from `config.json` with `#` comments; survives corrupt configs without any traceback; highscores save and load cleanly.

---

### 🟢 Day 6: Ghosts Spawning & Corridor Movement
**Goal:** Spawn 4 ghosts in 4 corners and have them move through corridors.

- [x] **Teammate A (Ghost Rendering & Entities):**
  - [x] Create sprites or colored shapes for 4 distinct ghosts (Red, Pink, Cyan, Orange).
  - [x] Draw ghosts at their positions.
- [x] **Teammate B (Ghost Physics & Life Management):**
  - [x] Implement `Ghost` base class with position and movement.
  - [x] Ghost corridor constraints: ghosts can only travel through corridors (no walls), can make choices at intersections.
  - [x] Implement player-ghost collision: player loses 1 life, respawns in center; game over when 0 lives remain.
- [x] **Pair Work (Both):**
  - [x] Verify all 4 ghosts patrol corridors without glitching through walls.
- [x] **Day 6 Done Criteria:** 4 ghosts roam the maze; touching a ghost costs 1 life and resets Pac-Man to the center.

---

### 🟢 Day 7: Ghost AI & Frightened / Eaten States
**Goal:** Implement chasing behavior, frightened mode on super-pacgum, and eating ghosts.

- [x] **Teammate A (Frightened Visuals & Respawn):**
  - [x] Visual indicator when ghosts are edible (turn blue / flashing).
  - [x] Eaten ghost state: show eyes or ghost returning/respawning in corner after delay (5–10s).
- [x] **Teammate B (AI & State Machine):**
  - [x] Implement `CHASE` state: target Pac-Man's tile (e.g. using distance heuristic / BFS pathfinding).
  - [x] Implement `FRIGHTENED` state: triggered when Pac-Man eats super-pacgum, ghosts reverse and pick random/away paths.
  - [x] Implement ghost eating: Pac-Man eats blue ghost -> awards bonus points -> ghost enters `EATEN` state.
- [x] **Pair Work (Both):**
  - [x] Fine-tune timer for frightened mode and ghost speeds.
- [x] **Day 7 Done Criteria:** Full Pac-Man gameplay loop working (chase -> super-pacgum -> eat ghost -> ghost respawns).

---

### 🟢 Day 8: Multi-Level Progression & Level Timer
**Goal:** Support 10+ levels with seed handling and countdown timers.

- [x] **Teammate A (Level Timer & Transition):**
  - [x] Implement countdown timer HUD (`level_max_time`, e.g. 90s).
  - [x] Handle time-out event (restart level or lose life).
- [x] **Teammate B (Progression Logic):**
  - [x] Level progression manager: Level 1 uses fixed seed (e.g. 42), levels 2–10+ use random seeds.
  - [x] Retain current score and remaining lives when transitioning to next level.
  - [x] Victory condition: winning after clearing level 10.
- [x] **Pair Work (Both):**
  - [x] Play through levels 1, 2, and 3 back-to-back to verify smooth transition and clean memory state.
- [x] **Day 8 Done Criteria:** Game seamlessly transitions across 10 levels with correct seeding and timers.

---

### 🟢 Day 9: User Interface & Screens
**Goal:** Build complete menu flows required by Chapter 6.8.

- [x] **Teammate A (Menus & Screens):**
  - [x] Main Menu: Start Game, View Highscores (Top 10), Instructions (Controls), Exit.
  - [x] Pause Menu: Resume, Return to Main Menu.
- [x] **Teammate B (End Screens & Input):**
  - [x] In-game HUD: Current score, Remaining lives, Current level, Remaining time.
  - [x] Game Over Screen & Victory Screen with final score.
  - [x] Name input prompt (saving top 10 highscore with sanitized alphanumeric name).
- [x] **Pair Work (Both):**
  - [x] Test the entire game loop: `Main Menu -> Play -> Win/Lose -> Name Entry -> Back to Main Menu`.
- [x] **Day 9 Done Criteria:** All 5 required screens operational with keyboard navigation.

---

### 🟢 Day 10: Cheat Mode Implementation
**Goal:** Add reviewer cheat features required by Chapter 6.5.

- [x] **Teammate A (Cheat Hotkeys & Feedback):**
  - [x] Bind dedicated cheat keys (e.g., `I` for Invincible, `L` for Level Skip, `F` for Freeze, `+` for Extra Life, `S` for Speed Boost).
  - [x] Add visual badge on HUD indicating active cheats (e.g., `[CHEAT: INVINCIBLE]`).
- [x] **Teammate B (Cheat State Integration):**
  - [x] Implement cheat logic toggles in `GameState`.
  - [x] Ensure cheat mode works in all levels without crashing.
- [x] **Pair Work (Both):**
  - [x] Test using cheats to skip from Level 1 to Level 10 and verify Victory screen triggers correctly.
- [x] **Day 10 Done Criteria:** Peer reviewers can easily test every game feature using intuitive cheat keys.

---

### 🟢 Day 11: Robustness Hardening & Strict Linting
**Goal:** Meet all Chapter 3 coding standards (flake8, mypy, PEP 257, zero crashes).

- [x] **Teammate A (Linting & Docstrings):**
  - [x] Run `flake8 .` and fix all formatting, line length, and syntax issues.
  - [x] Add PEP 257 docstrings to every class and function (Google or NumPy style).
- [x] **Teammate B (Type Hints & Exception Defense):**
  - [x] Add complete type annotations across all files.
  - [x] Run `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`.
  - [x] Audit all file I/O and resource usage (use context managers `with open(...)`).
  - [x] Test with bad CLI args (`python3 pac-man.py nonexistent.json`) -> verify clear error message, no traceback.
- [x] **Pair Work (Both):**
  - [x] Verify `make lint` exits with code 0.
- [x] **Day 11 Done Criteria:** Zero flake8 errors, zero mypy errors, zero uncaught exceptions under malformed inputs.

---

### 🟢 Day 12: Project Management Documentation (Chapter 8)
**Goal:** Compile required evidence of planning, team collaboration, and risk management.

- [x] **Teammate A (Organization & Test Plan):**
  - [x] Write `project_management/team_organization.md` (who built what, how decisions were made).
  - [x] Write `project_management/test_plan.md` (features tested, edge cases, bugs encountered and fixed).
- [x] **Teammate B (Timeline Tracking & Risk Analysis):**
  - [x] Fill out `project_management/timeline.md` comparing planned schedule vs. actual progress.
  - [x] Write `project_management/risk_analysis.md` (risks identified and mitigations applied).
  - [x] Write `project_management/retrospective.md` (blocking points and solutions).
- [x] **Pair Work (Both):**
  - [x] Review documents to ensure they meet Chapter 8 requirements.
- [x] **Day 12 Done Criteria:** `project_management/` folder contains comprehensive documentation ready for defense.

---

### 🟢 Day 13: Project Packaging & Release (Chapter 7)
**Goal:** Produce a standalone package and publish an unlisted release on Itch.io.

- [x] **Teammate A (Executable Build):**
  - [x] Write a packaging script/spec file at repository root using `PyInstaller`.
  - [x] Ensure assets, default config, and wheel dependencies are bundled properly.
  - [x] Test the built executable on a clean machine or fresh folder.
- [x] **Teammate B (Itch.io Deployment):**
  - [x] Create a free/unlisted project page on **Itch.io**.
  - [x] Upload the build ZIP.
  - [x] Include clear in-package instructions (controls, cheat keys, config usage).
- [x] **Pair Work (Both):**
  - [x] Download the build from Itch.io and verify it launches and plays without errors.
- [x] **Day 13 Done Criteria:** Working build accessible on Itch.io; packaging script committed at repo root.

---

### 🟢 Day 14: Final README & Peer-Review Simulation
**Goal:** Finalize documentation and rehearse the live evaluation.

- [x] **Teammate A & B (README.md):**
  - [x] Verify mandatory italicized first line:
    `*This activity has been created as part of the 42 curriculum by mewaysi, mal-jama.*`
  - [x] Write all mandatory sections: Description, Instructions, Resources (including detailed AI usage log), Configuration, Highscore, Maze Generation, Implementation, Architecture, Project Management link.
- [x] **Peer-Review Simulation (Defense Practice):**
  - [x] Reinstall the external wheel from scratch into a clean virtual environment.
  - [x] Run with broken config files (missing keys, letters instead of numbers, comments).
  - [x] Practice explaining individual components (ghost AI, adapter, config parser).
  - [x] Simulate live code modifications (e.g. changing ghost speed or pacgum points).
- [x] **Day 14 Done Criteria:** Project is 100% compliant, tested, packaged, and ready for submission!
