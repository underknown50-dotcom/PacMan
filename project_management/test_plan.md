# 🧪 Acceptance Test Plan & Quality Assurance Matrix

> **Project:** 42 Pac-Man  
> **Target:** Chapter 8 Project Management & Chapter 10 Peer-Review Readiness

---

## 1. Test Execution Summary

| Test Category | Test Cases | Automated / Manual | Result |
|---|:---:|:---:|:---:|
| **Configuration Resilience** | 4 | Automated (`tests/test_game.py`) | ✅ PASS |
| **Highscore Persistence** | 3 | Automated (`tests/test_game.py`) | ✅ PASS |
| **Maze Adapter & Bitmasks** | 3 | Automated (`tests/test_game.py`) | ✅ PASS |
| **Entity States & Cheats** | 2 | Automated (`tests/test_game.py`) | ✅ PASS |
| **Code Style (`flake8`)** | Entire Repo | Automated (`make lint`) | ✅ PASS (0 errors) |
| **Static Types (`mypy`)** | Entire Repo | Automated (`make lint-strict`) | ✅ PASS (0 errors) |
| **Interactive Gameplay** | 8 | Manual (Ubuntu WSL) | ✅ PASS |

---

## 2. Test Cases & Verification Matrix

### TC-01: Faulty Config Defense (Zero Traceback)
- **Objective:** Verify that missing keys, corrupt formatting, or negative numbers never cause an unhandled exception or Python traceback.
- **Inputs:**
  1. No CLI argument: `python3 pac-man.py`
  2. Non-JSON extension: `python3 pac-man.py config.txt`
  3. Non-existent file: `python3 pac-man.py missing.json`
  4. Corrupted JSON containing invalid values: `{"lives": -99, "points": "bad"}`
- **Expected Outcome:** Program outputs a clean warning message to `stdout`, clamps values to safe defaults, or exits cleanly with code 1. Zero tracebacks.
- **Status:** **VERIFIED & PASSED**

### TC-02: External Wheel Isolation
- **Objective:** Verify `MazeAdapter` works as-is with the original unedited wheel file.
- **Execution:** Reinstalled `wheels/mazegenerator-2.1.0-py3-none-any.whl` from scratch. Verified that `PERFECT=False` generates multi-corridor loops.
- **Status:** **VERIFIED & PASSED**

### TC-03: Highscore Validation
- **Objective:** Verify that names are sanitized to 10 alphanumeric characters/spaces and only top 10 scores persist.
- **Execution:** Added 15 consecutive scores with special characters (`"Player#1!$"`). Verified that only top 10 scores remain in descending order and special characters are stripped.
- **Status:** **VERIFIED & PASSED**

### TC-04: Peer-Review Cheat Suite
- **Objective:** Verify cheat hotkeys during live evaluation:
  - `I`: Toggle Invincibility (ghosts pass through without losing lives).
  - `L`: Skip Level (advances to next level immediately).
  - `F`: Freeze Ghosts (ghosts halt in corridors).
  - `+`: Extra Life (increments life count).
  - `S`: Speed Boost (speeds Pac-Man by 60%).
- **Status:** **VERIFIED & PASSED**

### TC-05: 10-Level Campaign Progression & Timer
- **Objective:** Verify game progresses across all 10 levels, seed 42 is used for level 1, random seeds for levels 2–10, and victory screen triggers upon clearing level 10.
- **Status:** **VERIFIED & PASSED**

---

## 3. Bugs Discovered & Resolved During Testing

| Bug ID | Component | Description & Root Cause | Resolution | Status |
|:---:|---|---|---|:---:|
| **BUG-01** | `pacman/game.py` | Clearing the maze by eating a super-pacgum as the final consumable did not trigger level completion because the check was only placed in the regular pacgum handler. | Added `_check_level_cleared()` logic to both pacgum and super-pacgum consumption branches. | ✅ Fixed |
| **BUG-02** | `pac-man.py` | Running the PyInstaller standalone build without CLI arguments triggered the Chapter 5.1 argument error, preventing double-click execution on Itch.io. | Detected `getattr(sys, 'frozen', False)`: if frozen and no arguments are given, auto-default to bundled `config.json`. | ✅ Fixed |
| **BUG-03** | `pacman/adapter.py` | The external maze generator places a solid `15` "42" logo in the exact center of odd-dimension mazes, trapping Pac-Man if spawned strictly at `(w//2, h//2)`. | Implemented BFS flood-fill (`find_safe_center`) to find the nearest open corridor tile from the mathematical center. | ✅ Fixed |
| **BUG-04** | `pacman/config.py` | JSON standard does not permit comments (`#`, `//`, `/* */`), causing standard `json.loads` to crash on human-edited configurations. | Built regex-aware pre-processing scanner that removes single-line and block comments without disturbing strings. | ✅ Fixed |
| **BUG-05** | `pacman/highscores.py` | Corrupted or manually truncated highscore file threw JSON decode error on launch. | Wrapped loader in `try-except json.JSONDecodeError` with automatic fallback to empty table and warning. | ✅ Fixed |

