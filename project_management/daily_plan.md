# 📅 Pac-Man Project: 14-Day Sprint & Daily To-Do Tracker

> **Project:** 42 Pac-Man (Team of 2)  
> **Duration:** 14 Days (Recommended 3–4 hours/day)  
> **Objective:** Deliver a complete, robust, type-safe Pac-Man game with custom level generator integration and deployment to Itch.io.

---

## 📊 Sprint Overview & Progress Matrix

| Day | Phase | Primary Objective | Status |
|:---:|:---|:---|:---:|
| **Day 1** | Foundation | Environment, Makefile, Wheel Inspection, Kanban setup | ✅ Done |
| **Day 2** | Adapter & Grid | Render static maze from external wheel | ⚪ Not Started |
| **Day 3** | Player Movement | Pac-Man controls, corridor navigation & grid collision | ⚪ Not Started |
| **Day 4** | Collectibles | Pacgums, Super-pacgums, and scoring logic | ⚪ Not Started |
| **Day 5** | Persistence & Config | Fault-tolerant JSON parser (# comments) & Highscores | ⚪ Not Started |
| **Day 6** | Ghost Basics | Ghost spawning, corridor movement, collision with player | ⚪ Not Started |
| **Day 7** | Ghost AI & States | Chase logic, Frightened mode, Eaten/Respawn timer | ⚪ Not Started |
| **Day 8** | Levels & Timer | 10+ levels progression, seeds (Level 1 fixed), time limits | ⚪ Not Started |
| **Day 9** | UI & Game Screens | Main Menu, HUD, Pause, Game Over, Victory screen | ⚪ Not Started |
| **Day 10** | Cheat Mode | Reviewer cheat hotkeys (Invincible, Skip, Freeze, etc.) | ⚪ Not Started |
| **Day 11** | Robustness & Quality | Zero traceback defense test, flake8 & mypy strict pass | ⚪ Not Started |
| **Day 12** | Project Management | Document timeline vs. actual, risk analysis, test plans | ⚪ Not Started |
| **Day 13** | Packaging & Release | Standalone build (PyInstaller) & upload to Itch.io | ⚪ Not Started |
| **Day 14** | README & Final Review | Complete README.md and mock peer-review defense | ⚪ Not Started |

---

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

- [ ] **Teammate A (Renderer):**
  - [ ] Define tile size (e.g. $24 \times 24$ or $32 \times 32$ pixels).
  - [ ] Implement `Renderer` class to draw blue wall tiles and empty corridor tiles on screen.
  - [ ] Add basic camera / window sizing calculation based on maze dimensions.
- [ ] **Teammate B (Adapter):**
  - [ ] Implement `MazeAdapter` class that wraps the external package without modifying it.
  - [ ] Convert whatever raw structure the wheel outputs into a clean internal 2D grid matrix `List[List[int]]`.
  - [ ] Handle potential errors from the generator cleanly (catch exceptions and provide safe fallback).
- [ ] **Pair Work (Both):**
  - [ ] Connect `MazeAdapter` to `Renderer`: launch the game and see the generated maze drawn on screen!
- [ ] **Day 2 Done Criteria:** Running `python3 pac-man.py` draws a complete generated maze on screen.

---

### 🟢 Day 3: Pac-Man Movement & Collision
**Goal:** Spawn Pac-Man in the center and allow smooth movement through corridors without walking through walls.

- [ ] **Teammate A (Input & Animation):**
  - [ ] Capture Arrow keys and WASD input in the event loop.
  - [ ] Draw Pac-Man (yellow circle or sprite) with orientation (facing direction).
  - [ ] Buffer input (so pressing Turn Right before an intersection queues the turn).
- [ ] **Teammate B (Movement Physics & Collision):**
  - [ ] Implement `Pacman` class (tracks grid coordinates `(x, y)`, direction `(dx, dy)`).
  - [ ] Implement tile collision logic: check if the destination cell in the grid is a wall.
  - [ ] Center spawn calculation: place player at `(width // 2, height // 2)`.
- [ ] **Pair Work (Both):**
  - [ ] Verify Pac-Man stops cleanly at walls and turns smoothly into corridors.
- [ ] **Day 3 Done Criteria:** Player can steer Pac-Man around the entire maze without passing through walls.

---

### 🟢 Day 4: Collectibles (Pacgums, Super-pacgums, Score)
**Goal:** Populate corridors with pacgums, place super-pacgums in corners, and collect them.

- [ ] **Teammate A (Visuals & Audio):**
  - [ ] Render small white dots (pacgums) in corridors.
  - [ ] Render larger pulsating dots (super-pacgums) in the 4 corners of the maze.
  - [ ] Simple score counter display at the bottom or top of the screen.
- [ ] **Teammate B (Game State Logic):**
  - [ ] Populate grid with pacgums on empty corridor tiles.
  - [ ] Locate the 4 accessible corner positions for super-pacgums.
  - [ ] Implement eating logic: when player coordinate == dot coordinate, award points and remove dot.
  - [ ] Level win condition: trigger level complete when all regular pacgums are eaten.
- [ ] **Pair Work (Both):**
  - [ ] Test that collecting every dot clears the maze and triggers a win event.
- [ ] **Day 4 Done Criteria:** All corridors have pacgums, corners have super-pacgums, eating them awards points, and clearing dots detects level completion.

---

### 🟢 Day 5: Fault-Tolerant Config & Persistent Highscores
**Goal:** Build the comment-supporting config parser and the highscore JSON system.

- [ ] **Teammate A (Config Parser):**
  - [ ] Create `ConfigLoader`: reads JSON file but ignores lines starting with `#`.
  - [ ] Implement safe defaults for every single key (`lives: 3`, `points_per_pacgum: 10`, `level_max_time: 90`, etc.).
  - [ ] Defensive validation: if a key is missing, invalid type, or out of range, clamp to safe default, print warning, and **do not crash**.
  - [ ] Unknown keys must be ignored without raising errors.
- [ ] **Teammate B (Highscore System):**
  - [ ] Create `HighscoreManager`: persistent storage in a JSON file.
  - [ ] Validate player names: max 10 characters, alphanumeric and spaces only.
  - [ ] Ensure scores are non-negative integers.
  - [ ] Keep and sort top 10 scores; handle missing/corrupted highscore file gracefully.
- [ ] **Pair Work (Both):**
  - [ ] Write unit tests / scratch tests trying to break the config and highscore files with bad inputs.
- [ ] **Day 5 Done Criteria:** Program loads game parameters from `config.json` with `#` comments; survives corrupt configs without any traceback; highscores save and load cleanly.

---

### 🟢 Day 6: Ghosts Spawning & Corridor Movement
**Goal:** Spawn 4 ghosts in 4 corners and have them move through corridors.

- [ ] **Teammate A (Ghost Rendering & Entities):**
  - [ ] Create sprites or colored shapes for 4 distinct ghosts (Red, Pink, Cyan, Orange).
  - [ ] Draw ghosts at their positions.
- [ ] **Teammate B (Ghost Physics & Life Management):**
  - [ ] Implement `Ghost` base class with position and movement.
  - [ ] Ghost corridor constraints: ghosts can only travel through corridors (no walls), can make choices at intersections.
  - [ ] Implement player-ghost collision: player loses 1 life, respawns in center; game over when 0 lives remain.
- [ ] **Pair Work (Both):**
  - [ ] Verify all 4 ghosts patrol corridors without glitching through walls.
- [ ] **Day 6 Done Criteria:** 4 ghosts roam the maze; touching a ghost costs 1 life and resets Pac-Man to the center.

---

### 🟢 Day 7: Ghost AI & Frightened / Eaten States
**Goal:** Implement chasing behavior, frightened mode on super-pacgum, and eating ghosts.

- [ ] **Teammate A (Frightened Visuals & Respawn):**
  - [ ] Visual indicator when ghosts are edible (turn blue / flashing).
  - [ ] Eaten ghost state: show eyes or ghost returning/respawning in corner after delay (5–10s).
- [ ] **Teammate B (AI & State Machine):**
  - [ ] Implement `CHASE` state: target Pac-Man's tile (e.g. using distance heuristic / BFS pathfinding).
  - [ ] Implement `FRIGHTENED` state: triggered when Pac-Man eats super-pacgum, ghosts reverse and pick random/away paths.
  - [ ] Implement ghost eating: Pac-Man eats blue ghost -> awards bonus points -> ghost enters `EATEN` state.
- [ ] **Pair Work (Both):**
  - [ ] Fine-tune timer for frightened mode and ghost speeds.
- [ ] **Day 7 Done Criteria:** Full Pac-Man gameplay loop working (chase -> super-pacgum -> eat ghost -> ghost respawns).

---

### 🟢 Day 8: Multi-Level Progression & Level Timer
**Goal:** Support 10+ levels with seed handling and countdown timers.

- [ ] **Teammate A (Level Timer & Transition):**
  - [ ] Implement countdown timer HUD (`level_max_time`, e.g. 90s).
  - [ ] Handle time-out event (restart level or lose life).
- [ ] **Teammate B (Progression Logic):**
  - [ ] Level progression manager: Level 1 uses fixed seed (e.g. 42), levels 2–10+ use random seeds.
  - [ ] Retain current score and remaining lives when transitioning to next level.
  - [ ] Victory condition: winning after clearing level 10.
- [ ] **Pair Work (Both):**
  - [ ] Play through levels 1, 2, and 3 back-to-back to verify smooth transition and clean memory state.
- [ ] **Day 8 Done Criteria:** Game seamlessly transitions across 10 levels with correct seeding and timers.

---

### 🟢 Day 9: User Interface & Screens
**Goal:** Build complete menu flows required by Chapter 6.8.

- [ ] **Teammate A (Menus & Screens):**
  - [ ] Main Menu: Start Game, View Highscores (Top 10), Instructions (Controls), Exit.
  - [ ] Pause Menu: Resume, Return to Main Menu.
- [ ] **Teammate B (End Screens & Input):**
  - [ ] In-game HUD: Current score, Remaining lives, Current level, Remaining time.
  - [ ] Game Over Screen & Victory Screen with final score.
  - [ ] Name input prompt (saving top 10 highscore with sanitized alphanumeric name).
- [ ] **Pair Work (Both):**
  - [ ] Test the entire game loop: `Main Menu -> Play -> Win/Lose -> Name Entry -> Back to Main Menu`.
- [ ] **Day 9 Done Criteria:** All 5 required screens operational with keyboard navigation.

---

### 🟢 Day 10: Cheat Mode Implementation
**Goal:** Add reviewer cheat features required by Chapter 6.5.

- [ ] **Teammate A (Cheat Hotkeys & Feedback):**
  - [ ] Bind dedicated cheat keys (e.g., `I` for Invincible, `L` for Level Skip, `F` for Freeze, `+` for Extra Life, `S` for Speed Boost).
  - [ ] Add visual badge on HUD indicating active cheats (e.g., `[CHEAT: INVINCIBLE]`).
- [ ] **Teammate B (Cheat State Integration):**
  - [ ] Implement cheat logic toggles in `GameState`.
  - [ ] Ensure cheat mode works in all levels without crashing.
- [ ] **Pair Work (Both):**
  - [ ] Test using cheats to skip from Level 1 to Level 10 and verify Victory screen triggers correctly.
- [ ] **Day 10 Done Criteria:** Peer reviewers can easily test every game feature using intuitive cheat keys.

---

### 🟢 Day 11: Robustness Hardening & Strict Linting
**Goal:** Meet all Chapter 3 coding standards (flake8, mypy, PEP 257, zero crashes).

- [ ] **Teammate A (Linting & Docstrings):**
  - [ ] Run `flake8 .` and fix all formatting, line length, and syntax issues.
  - [ ] Add PEP 257 docstrings to every class and function (Google or NumPy style).
- [ ] **Teammate B (Type Hints & Exception Defense):**
  - [ ] Add complete type annotations across all files.
  - [ ] Run `mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs`.
  - [ ] Audit all file I/O and resource usage (use context managers `with open(...)`).
  - [ ] Test with bad CLI args (`python3 pac-man.py nonexistent.json`) -> verify clear error message, no traceback.
- [ ] **Pair Work (Both):**
  - [ ] Verify `make lint` exits with code 0.
- [ ] **Day 11 Done Criteria:** Zero flake8 errors, zero mypy errors, zero uncaught exceptions under malformed inputs.

---

### 🟢 Day 12: Project Management Documentation (Chapter 8)
**Goal:** Compile required evidence of planning, team collaboration, and risk management.

- [ ] **Teammate A (Organization & Test Plan):**
  - [ ] Write `project_management/team_organization.md` (who built what, how decisions were made).
  - [ ] Write `project_management/test_plan.md` (features tested, edge cases, bugs encountered and fixed).
- [ ] **Teammate B (Timeline Tracking & Risk Analysis):**
  - [ ] Fill out `project_management/timeline.md` comparing planned schedule vs. actual progress.
  - [ ] Write `project_management/risk_analysis.md` (risks identified and mitigations applied).
  - [ ] Write `project_management/retrospective.md` (blocking points and solutions).
- [ ] **Pair Work (Both):**
  - [ ] Review documents to ensure they meet Chapter 8 requirements.
- [ ] **Day 12 Done Criteria:** `project_management/` folder contains comprehensive documentation ready for defense.

---

### 🟢 Day 13: Project Packaging & Release (Chapter 7)
**Goal:** Produce a standalone package and publish an unlisted release on Itch.io.

- [ ] **Teammate A (Executable Build):**
  - [ ] Write a packaging script/spec file at repository root using `PyInstaller`.
  - [ ] Ensure assets, default config, and wheel dependencies are bundled properly.
  - [ ] Test the built executable on a clean machine or fresh folder.
- [ ] **Teammate B (Itch.io Deployment):**
  - [ ] Create a free/unlisted project page on **Itch.io**.
  - [ ] Upload the build ZIP.
  - [ ] Include clear in-package instructions (controls, cheat keys, config usage).
- [ ] **Pair Work (Both):**
  - [ ] Download the build from Itch.io and verify it launches and plays without errors.
- [ ] **Day 13 Done Criteria:** Working build accessible on Itch.io; packaging script committed at repo root.

---

### 🟢 Day 14: Final README & Peer-Review Simulation
**Goal:** Finalize documentation and rehearse the live evaluation.

- [ ] **Teammate A & B (README.md):**
  - [ ] Verify mandatory italicized first line:
    `*This activity has been created as part of the 42 curriculum by <login1>, <login2>.*`
  - [ ] Write all mandatory sections: Description, Instructions, Resources (including detailed AI usage log), Configuration, Highscore, Maze Generation, Implementation, Architecture, Project Management link.
- [ ] **Peer-Review Simulation (Defense Practice):**
  - [ ] Reinstall the external wheel from scratch into a clean virtual environment.
  - [ ] Run with broken config files (missing keys, letters instead of numbers, comments).
  - [ ] Practice explaining individual components (ghost AI, adapter, config parser).
  - [ ] Simulate live code modifications (e.g. changing ghost speed or pacgum points).
- [ ] **Day 14 Done Criteria:** Project is 100% compliant, tested, packaged, and ready for submission!
