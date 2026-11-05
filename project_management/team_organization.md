# 👥 Team Organization & Responsibility Matrix

> **Team Members:** `mewaysi` & `mal-jama`  
> **Project:** 42 Pac-Man

---

## 1. Roles & Core Responsibilities

| Area | Primary Owner | Secondary / Reviewer | Key Responsibilities |
|---|:---:|:---:|---|
| **Engine & Graphics** | `mewaysi` | `mal-jama` | Pygame window, Rendering pipeline, Tile drawing, UI Menus, HUD |
| **Maze Adapter & Wheel** | `mal-jama` | `mewaysi` | External wheel integration (`mazegenerator`), data translation, grid format |
| **Game Physics & Collision** | `mal-jama` | `mewaysi` | Pac-Man corridor movement, collision math, corner placement |
| **Ghost AI & Behaviors** | `mal-jama` | `mewaysi` | State machine (`CHASE`, `FRIGHTENED`, `EATEN`), targeting logic, respawn |
| **Config & Persistence** | `mewaysi` | `mal-jama` | Comment-aware JSON parser (`#`), default clamping, Highscore JSON |
| **Cheat System** | `mal-jama` | `mewaysi` | Peer-review cheat keybindings (Invincibility, Level Skip, Freeze) |
| **Packaging & Deployment**| `mewaysi` | `mal-jama` | PyInstaller standalone packaging, Itch.io upload & testing |
| **Quality & Standards** | Both | Both | `flake8` compliance, `mypy` strict typing, PEP 257 docstrings |

---

## 2. Decision-Making & Conflict Resolution
- **Technical Disagreements:** If we debate an architectural choice (e.g., how to represent tiles or state), we test both with a quick 15-minute prototype and choose the simpler, more testable option.
- **Git Strategy:** All new work is done on feature branches (e.g. `feature/adapter`, `feature/ghosts`). Merging into `main` requires both teammates' review and passing `make lint`.
- **Daily Standup:** At the beginning of each session, spend 5 minutes reviewing yesterday's tasks and confirming today's to-do items from `daily_plan.md`.
