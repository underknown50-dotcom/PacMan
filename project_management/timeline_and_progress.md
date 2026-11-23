# Timeline and Actual Progress

## Planned vs. Actual Milestones

| Phase | Goal | Planned | Actual | Status |
| --- | --- | --- | --- | :---: |
| **1. Setup & Contracts** | Read subject, inspect `mazegenerator` wheel API, set up `Makefile`, `.flake8`, `mypy.ini`, and MVC layout | Day 1–2 | Day 1–2 | Done |
| **2. Config & Persistence** | Comment-aware JSON parser (`#`), case-insensitive keys, safe clamping, and atomic top-10 highscores | Day 3–4 | Day 3–4 | Done |
| **3. Maze & Core Engine** | Unmodified `MazeGenerator(perfect=False)` adapter, 4-bit wall graph, BFS distances, `Actor` smooth movement, collisions, and 10 levels | Day 5–7 | Day 5–8 | Done |
| **4. Ghost AI & Cheats** | Blinky/Pinky/Inky/Clyde targeting, frightened fleeing, returning BFS eyes, respawn cooldown, and `F1` review mode | Day 8–9 | Day 8–9 | Done |
| **5. UI & MLX Facade** | Restricted MLX-equivalent `graphics.py`, custom pixel rasterization, HUD, animated menus, Victory/Game Over screens, and rotating error logs | Day 10–11 | Day 10–12 | Done |
| **6. Packaging & QA** | PyInstaller standalone Linux bundle (`make release`), strict lint/typing, clean `.gitignore`, and itch.io release preparation | Day 12 | Day 12–13 | Done |

## Schedule Adjustments Made Along the Way

- **Maze Adapter (+1 day):** Inspecting the actual `mazegenerator` wheel revealed it uses `size=(width, height)` and embeds sealed mask-15 `"42"` cells. We spent an extra day adding BFS largest-component filtering and safe spawn/corner selection without modifying the wheel.
- **UI & Visual Polish (+1 day):** We added desktop auto-scaling (down to 640×544), animated twilight/victory/game-over backgrounds with layer caching, and returning ghost eyes so every game state is immediately clear on screen.
