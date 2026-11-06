# Pac-Man 42 — Team Study & Defense Responsibilities

**Team members:** `mal-jama` and `mewaysi`  
**Project:** completed Pac-Man game (current repository)  
**Reference:** `en.subject-3.pdf` / 42 Pacman subject v1.5  
**Purpose:** Divide **code understanding, explanation, testing, and defense preparation** between the two team members. **The game has already been implemented.** This is **not** a request to rebuild it.

> **For the team and reviewers:** Use the **actual files in this repository** when studying and explaining the current implementation. The assignments below cover **studying, testing and presenting** each part. They do not attribute original implementation authorship. Study preparation does not require changing the game code.

## 1. Final reversed assignment

| Member | Assigned part | Core focus | Relative difficulty |
|---|---|---|---|
| **`mal-jama`** | **Part 2 — UI, Application, Configuration, Highscores & Release** | What the player sees, how the program launches, settings, menus, results, build, release and documentation | ~6.5/10 |
| **`mewaysi`** | **Part 1 — Game Engine, Maze, Player, Ghost AI & Gameplay** | How the game works internally: maze, movement, collisions, AI, levels, scoring, powers and cheats | ~8/10 |

*Difficulty is an informal study estimate, not an official 42 grade.*

---

## 2. `mal-jama` — Part 2: UI / Application / Configuration / Highscores / Release

### What this part means

Explain the **application lifecycle and player-facing side** of the completed game: start-up, windows, keyboard events, drawing, navigation between screens, configuration parsing, recovering from errors, storing highscores and preparing a distributable game.

### Primary source files — understand in depth

| Priority | Actual path | Explain / be ready to modify |
|---|---|---|
| **P0** | `pac-man.py` | CLI entry point, argument validation, config loading, initial score loading, main application startup and error handling. |
| **P0** | `pacman/app.py` | `App`, game loop (`run`), user input (`handle`), menu navigation, starting games, forwarding inputs to the model, score-entry flow and screen selection (`draw`). |
| **P0** | `pacman/rendering.py` | `Renderer`, rendering the board, player, ghosts, HUD, menu, instructions, scores, pause, victory, loss and error screens. |
| **P0** | `pacman/graphics.py` | Restricted pygame graphics facade, window lifecycle, graphics primitives, keyboard/text event normalization, frame timing, drawing and screenshot support; explain the subject's MLX-equivalence restriction. |
| **P1** | `pacman/menu_background.py` | `GardenBackground`, cached scenery, monotonic animation time and separation from gameplay timers. |
| **P1** | `pacman/finish_background.py` | `FinishBackground`, distinct victory/loss gardens, cached scenery and independent decorative animation. |
| **P1** | `pacman/error_logging.py` | `ErrorLogSession`, rotating UTC log, brief console messages, graceful file failures and handler cleanup. |
| **P0** | `pacman/configuration.py` | `GameConfig`, `LevelConfig`, JSON with `#` comments, defaults, validation/clamping, errors, level configuration and writable highscore path resolution. |
| **P0** | `pacman/highscores.py` | `ScoreEntry`, `HighScoreStore`, name validation, sorted top-ten scores, JSON load/save, persistence and file-error handling. |
| **P1** | `config.json` | Main configuration values, per-level settings, score and timing parameters. |
| **P1** | `config.comments.json` | Working example of JSON with `#` comments and ignored unknown keys. |
| **P1** | `Makefile` | `install`, `run`, `debug`, `clean`, `lint`, `lint-strict`, `test`, `smoke`, `release`. |
| **P1** | `requirements.txt` | Runtime dependencies, including the locally supplied maze-generator wheel. |
| **P1** | `requirements-dev.txt` | Test, lint, type-checking and packaging tools. |
| **P1** | `pacman.spec` | PyInstaller packaging configuration, bundled data and executable build. |
| **P1** | `build_release.sh` | Reproducible Linux release build/archive process. |
| **P1** | `README.md` | How to install/run, configuration, graphics/MLX reasoning, architecture, highscore, maze integration and project requirements. |
| **P1** | `PLAYER_GUIDE.txt` | Player controls, game instructions and review-oriented commands. |
| **P2** | `.flake8`, `mypy.ini`, `.gitignore` | Code-quality configuration and ignored files. |
| **P2** | `tools/clean.py` | Cleanup script used by `make clean`. |
| **P2** | `tools/verify_integrity.py` | How source/dependency integrity is checked without changing the assigned maze-generator package. |

### Tests assigned to `mal-jama`

- `dev_tests/test_application.py` — CLI, UI, events, screens and error recovery.
- `dev_tests/test_configuration.py` — malformed/missing/changed settings, fallback values, path handling.
- `dev_tests/test_highscores.py` — valid/invalid player names, highscore ordering, corrupted or missing files, persistence.
- `dev_tests/test_error_logging.py` and `dev_tests/test_logging_integration.py` — persistent diagnostics, rotation, failure recovery and launcher/UI integration.
- `dev_tests/test_finish_screens.py` — distinct end screens, readable controls and eye rendering at both window sizes.
- **Shared edge-test subset:** in `dev_tests/test_review_edges.py`, study `test_native_keys_and_text_do_not_duplicate_name_characters` and `test_finishing_cheat_does_not_type_its_key_into_name` because they cover keyboard/text behavior in the UI.

### What `mal-jama` must be able to explain during defense

1. What happens from `python3 pac-man.py config.json` until the main menu appears.
2. How `App.run()` processes time, input, model updates and rendering.
3. How menus and end-of-game name entry work, including input validation and returning to the main menu.
4. How a keypress is translated into a request to the game engine, **without** needing to implement ghost pathfinding.
5. How drawing occurs through `Renderer` and the restricted `Graphics` facade.
6. How `#`-commented JSON is parsed and how bad config values are handled cleanly.
7. How highscores persist between runs and recover from missing/bad files.
8. How to lint, test, build, package and explain release/public-platform requirements.

---

## 3. `mewaysi` — Part 1: Game Engine / Maze / Player / Ghost AI / Gameplay

### What this part means

Explain the **gameplay implementation** independently of the UI: loading a maze from the school-provided package, movement without crossing walls, player/ghost simulation, chasing/fleeing, collisions, power pellets, scores, remaining lives, timed levels, victory/defeat and review cheats.

### Primary source files — understand in depth

| Priority | Actual path | Explain / be ready to modify |
|---|---|---|
| **P0** | `pacman/models.py` | `Game`, `State`, `Actor`, `Ghost`; complete gameplay rules, simulation/update timing, movement, collision detection, lives, scoring, pellets, timers, progression and cheat actions. **Most important gameplay file.** |
| **P0** | `pacman/maze_adapter.py` | `Maze`, `Direction`, `MazeError`; generator API, maze-wall bitmasks, allowed connections, graph/neighbors, distances, valid spawns, reachability and error handling. |
| **P0** | `pacman/ghost_ai.py` | `choose_step`, shortest-distance chase, frightened flee, tie-breaking, preventing unjustified reversal and legal passage selection. |
| **P0** | `pacman/cheats.py` | `Cheats`, enabled/invincible/frozen state; read its use in `Game.cheat()` in `models.py` for the complete behavior. |
| **P1** | `vendor/mazegenerator-2.1.0-py3-none-any.whl` | **Assigned school package**. Understand its public interface and input/output as consumed by `maze_adapter.py`. **Do not edit or replace it.** |
| **P1** | `../mazegenerator-00001(1).zip` | Original supplied maze-generator archive beside the project folder, for understanding the external resource and verifying provenance. |
| **P1** | `config.json` | Read the engine-facing configuration (levels, dimensions, lives, seed, speeds, time limits, scoring, power duration). |
| **P2** | `pacman/__init__.py` | Python package layout. |

### Tests assigned to `mewaysi`

- `dev_tests/test_models.py` — movement, collisions, powers, lives, scores, fixed-step simulation, levels, pause and cheats.
- `dev_tests/test_returning_ghosts.py` — continuous legal eye returns, harmlessness, cooldown, pause/freeze and fresh-run state.
- `dev_tests/test_maze.py` — generator integration, wall geometry, connectivity, placement, seeds, ghost decision-making and failure cases.
- **Shared edge-test subset:** in `dev_tests/test_review_edges.py`, own the movement, ghost, invincibility, pellets, level skip and timing tests (all except the two UI/text tests assigned above to `mal-jama`).

### What `mewaysi` must be able to explain during defense

1. How the **unchanged school-provided** `MazeGenerator` is called using `perfect=False` and the output is adapted.
2. How wall bitmasks define legal movement, and how reachability/neighbor data is computed.
3. Why the first level uses a repeatable seed and later levels are randomized.
4. How starting positions, four ghosts and four super-pacgums are selected safely.
5. How the player moves, turns, cannot cross walls, and loses/respawns with lives.
6. How ghosts chase using maze distances, flee during power mode, and return as harmless eyes through legal passages before their corner respawn.
7. How small and super-pacgums update the score, frightened state and timers.
8. How the clock, pause, at least ten levels and final win/loss are managed.
9. How cheat mode operates in `Game.cheat()`, and how it assists the 42 reviewer.
10. How to test wall collisions, moving in corners, timers, edge cases and generator failures.

---

## 4. Shared files and integration knowledge — BOTH MEMBERS

| Path | Joint requirement | Presentation lead |
|---|---|---|
| `en.subject-3.pdf` | Read the original 42 subject, especially Chapters 3–10. | Both |
| `pacman/app.py` ↔ `pacman/models.py` | Understand **how input/events flow into the engine and engine state flows back to the renderer**. | `mal-jama` explains the application; `mewaysi` explains the model. |
| `pacman/smoke.py` | End-to-end diagnostic that exercises application and gameplay together. | Both |
| `dev_tests/test_review_edges.py` | Split the specific tests as described in the individual parts. | Both |
| `project_management/README.md`, `plan.md`, `progress.md`, `decisions.md`, `risks.md`, `acceptance_tests.md`, `issues.md` | Understand project-management documentation, evidence, acceptance tests, decisions, risks, and actual history. | Both |
| `project_management/artifact_hashes.json`, `pacing_check.json` | Understand evidence for code/resource integrity and pacing checks. | `mewaysi` leads; `mal-jama` can explain how the verification tooling is invoked. |
| `project_management/release_check.json`, `final_verification.json` | Understand release/testing evidence. | `mal-jama` leads. |
| `project_management/screenshots/` | Reference examples of menu, play, pause, victory, loss, scores and instructions screens. | Both |
| `README.md` | Know the required 42 README sections, even if one member studies its details. | Both; `mal-jama` leads. |

### Essential integration map

```text
pac-man.py
    |
    v
pacman/app.py  --------------------->  pacman/rendering.py
    |                                       |
    |                                       v
    |                               pacman/graphics.py
    v
pacman/models.py  ---> pacman/ghost_ai.py
    |          \
    |           ---> pacman/cheats.py
    v
pacman/maze_adapter.py
    |
    v
school-supplied mazegenerator wheel

Supporting services:
  pacman/configuration.py  -> game settings + launch validation
  pacman/highscores.py     -> persistent top-ten scores
  pacman/error_logging.py  -> rotating diagnostics + brief console fallback
```

**Boundary:** `mal-jama` does not need to memorize how the ghost-distance algorithm works, but must know how the application requests movement and reads game state. `mewaysi` does not need to memorize rendering primitives, but must know how `App` calls the `Game` model and how changes reach the screen.

## 5. Recommended study sequence

| Step | `mal-jama` | `mewaysi` |
|---|---|---|
| 1 | `pac-man.py`, `pacman/app.py` | `pacman/models.py` |
| 2 | `pacman/graphics.py`, `pacman/rendering.py` | `pacman/maze_adapter.py`, assigned wheel |
| 3 | `pacman/configuration.py`, `config*.json` | `pacman/ghost_ai.py`, `pacman/cheats.py` |
| 4 | `pacman/highscores.py` | `dev_tests/test_models.py` |
| 5 | UI/config/highscore tests | `dev_tests/test_maze.py`, gameplay edge tests |
| 6 | `Makefile`, `pacman.spec`, `build_release.sh`, README | Shared smoke/integration testing |
| 7 | Joint review of the subject and project-management documents | Joint review of the subject and project-management documents |

## 6. 42 school requirements to remember

- Python 3.10+; flake8; mypy; type hints; docstrings; graceful error handling.
- CLI launch with **exactly one** JSON configuration argument.
- JSON files may contain `#` comments; invalid/missing settings must be handled cleanly.
- Use the **assigned external A-Maze-ing package as-is**, with `perfect=False`; the library may be reinstalled in peer review.
- The GUI must comply with the subject's **MLX-or-equivalent-functions** limitation.
- At least **10 levels**, persistent top-10 highscores, player-name rules and a useful cheat mode.
- Menus, always-visible HUD, pause, win/loss, name entry and return to main menu.
- Packaging and actual free/unlisted deployment to an eligible public gaming platform are part of the subject; **an archive alone does not prove a deployment**.
- README must be in English and start with the required 42 login line.
- Document real team responsibilities and review evidence truthfully; don't rewrite historical documents to invent past contributions.

## 7. Joint review preparation

1. Verify that the listed files exist in the current repository. Use actual
   paths and function/class names when explaining implementation behavior.
2. Keep the agreed split: **mal-jama = Part 2** and **mewaysi = Part 1**.
3. Separate the subject's requirement from the current code's behavior and any
   remaining gap or risk.
4. Each member should walk through their primary files, explain important
   functions/classes, show cross-module calls, run assigned tests and prepare
   realistic oral-defense questions.
5. Both members should explain how `App` passes input/time to `Game` and how
   model state reaches `Renderer` and `Graphics`.
6. Practice small changes appropriate to each member's assigned modules in a
   separate working copy. Record the trigger, affected code and validation.
7. Preserve the assigned wheel, original subject PDF and original resource
   archive. The team adapts to the generator's interface, never the reverse.
8. Keep team credits, review evidence and release status accurate. Record
   completed peer review and publication only after they actually happen.

### mal-jama preparation checklist

Follow the Part 2 study order. Trace startup and menu navigation, inspect the
rendering and graphics facade, explain the garden's independent animation,
walk through configuration/highscore error handling, then rehearse lint,
packaging and release commands. Prepare changes such as a menu label, a safe
configuration bound or score-entry feedback.

### mewaysi preparation checklist

Follow the Part 1 study order. Explain the real maze-package call and wall
bits, trace continuous movement and collisions, describe BFS chasing/fleeing,
then rehearse scoring, powers, countdowns, pause, progression and cheats.
Prepare changes such as a ghost-speed setting or a power-duration rule.

---

**Final reminder:** These assignments organize responsibility for understanding,
testing and presenting the existing project. They do not establish individual
original file authorship. Both members must understand the application's
purpose and how their assigned parts interact.
