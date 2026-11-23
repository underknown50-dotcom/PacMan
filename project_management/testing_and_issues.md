# Acceptance Tests and Resolved Issues

## 1. Acceptance Test Checklist

| Area | What Was Tested | Result |
| --- | --- | :---: |
| **Code Quality** | `make lint` (`flake8 .` + `mypy`) and `make lint-strict` (`mypy . --strict`) | PASS (0 errors) |
| **CLI & Error Handling** | 0 args, 2 args, missing file, malformed JSON, display failure (no tracebacks) | PASS |
| **Configuration** | `#` comments (`config.comments.json`), uppercase keys (`LIVES`), negative/bool values, unknown keys, `< 10` levels | PASS |
| **Maze Integration** | Unmodified `mazegenerator` wheel (`perfect=False`), fixed Level 1 seed (`42`), random later levels, wheel reinstall | PASS |
| **Gameplay & Ghosts** | Arrows/WASD movement, wall blocking, pellets (`+10`), super-pellets (`+50`), fleeing & eaten eyes (`+200`), respawn & 2s shield | PASS |
| **Cheats (`F1`)** | `I` (god), `N` (next level), `G` (freeze), `L` (+life), `B` (boost), `O` (power), `C` (1 pellet left), `T` (1s timer), `K` (lose life) | PASS |
| **UI & Persistence** | Main menu, HUD, Pause + confirm leave, Victory & Game Over screens, empty-to-saved highscore restart persistence | PASS |
| **Headless Smoke & Release** | `make smoke` (10 levels end-to-end) and `make release` (`./dist/Pacman42-Linux/run.sh`) | PASS |

## 2. Key Bugs Found and Fixed

| Issue Encountered | How We Fixed It |
| --- | --- |
| **Generator constructor mismatch** | The actual wheel takes `size=(w, h)` instead of `width=` / `height=` keywords; updated `maze_adapter.py` to match the real public API. |
| **Corner ghost & super-pellet overlap** | Reserved the 4 ghost corner spawns first, then placed the 4 super-pellets on the nearest remaining distinct cells. |
| **Python `bool` accepted as `int` in JSON** | Added explicit `isinstance(value, bool)` rejection in `configuration.py` and `highscores.py`. |
| **`N` cheat key leaked into Victory name input** | Suppressed the trailing text event from the level-finishing keypress in `app.py` so the name box starts cleanly empty. |
| **Larger later mazes tight on 90s timer** | Added per-level `level_max_time` scaling (180s up to 400s for Level 10) in `config.json`. |
| **Multiple damage hits in one collision** | Applied 2 seconds of post-respawn invulnerability and marked eaten ghosts inactive immediately so points/lives change strictly once. |
