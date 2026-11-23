# Team Organization

**Team Members:** `mewaysi` and `mal-jama`

## 1. Division of Responsibilities

We split the project along clean MVC boundaries so both teammates could work in parallel with minimal merge conflicts:

| Member | Role | Owned Modules |
| --- | --- | --- |
| **`mewaysi`** | **Part 1 — Game Engine, Maze & Gameplay** | `pacman/models.py`, `pacman/ghost_ai.py`, `pacman/maze_adapter.py`, `pacman/cheats.py` |
| **`mal-jama`** | **Part 2 — UI, Application, Services & Release** | `pac-man.py`, `pacman/app.py`, `pacman/graphics.py`, `pacman/rendering.py`, `pacman/configuration.py`, `pacman/highscores.py`, `pacman/error_logging.py`, `build_release.sh`, `pacman.spec` |
| **Both** | **Integration & Quality** | `Makefile`, `README.md`, `flake8` / `mypy --strict`, headless smoke tests, and joint defense prep |

## 2. How We Worked Together

- **Shared Interfaces:** `App` (`mal-jama`) communicates with `Game` (`mewaysi`) only through public methods (`start()`, `set_direction()`, `update(dt)`, `pause()`, `cheat()`). Neither side mutates the other's internals directly.
- **Decision Making:** When evaluating two technical options (for example, how to handle wall masks or highscore storage), we compared simplicity, testability, and strict compliance with the 42 subject before committing.
- **Code Quality Gate:** Every change had to pass `make lint` (`flake8` + `mypy`), `make lint-strict`, and `make smoke` before being merged.
