# 👥 Team Organization & Responsibility Matrix

> **Team:** Team of Two  
> **Project:** 42 Pac-Man

---

## 1. Roles & Core Responsibilities

| Area | Primary Owner | Secondary / Reviewer | Key Responsibilities |
|---|:---:|:---:|---|
| **Engine & Graphics** | Teammate A | Teammate B | Pygame window, Rendering pipeline, Tile drawing, UI Menus, HUD |
| **Maze Adapter & Wheel** | Teammate B | Teammate A | External wheel integration (`mazegenerator`), data translation, grid format |
| **Game Physics & Collision** | Teammate B | Teammate A | Pac-Man corridor movement, collision math, corner placement |
| **Ghost AI & Behaviors** | Teammate B | Teammate A | State machine (`CHASE`, `FRIGHTENED`, `EATEN`), targeting logic, respawn |
| **Config & Persistence** | Teammate A | Teammate B | Comment-aware JSON parser (`#`), default clamping, Highscore JSON |
| **Cheat System** | Teammate B | Teammate A | Peer-review cheat keybindings (Invincibility, Level Skip, Freeze) |
| **Packaging & Deployment**| Teammate A | Teammate B | PyInstaller standalone packaging, Itch.io upload & testing |
| **Quality & Standards** | Both | Both | `flake8` compliance, `mypy` strict typing, PEP 257 docstrings |

---

## 2. Decision-Making & Conflict Resolution
- **Technical Disagreements:** If we debate an architectural choice (e.g., how to represent tiles or state), we test both with a quick 15-minute prototype and choose the simpler, more testable option.
- **Git Strategy:** All new work is done on feature branches (e.g. `feature/adapter`, `feature/ghosts`). Merging into `main` requires both teammates' review and passing `make lint`.
- **Daily Standup:** At the beginning of each session, spend 5 minutes reviewing yesterday's tasks and confirming today's to-do items from `daily_plan.md`.
