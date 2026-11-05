# ⚠️ Risk Analysis & Mitigation Matrix

| Risk ID | Description & Potential Impact | Likelihood | Impact | Mitigation Strategy |
|:---:|---|:---:|:---:|---|
| **R1** | **Faulty Config Crash During Defense**<br>Evaluator alters `config.json` with invalid types, missing keys, or syntax errors, causing an unhandled Python traceback (instant fail). | High | Critical | Build a defensive `ConfigLoader` with strict try-except blocks, a fallback dictionary of safe defaults, and clamping logic. Test with dirty configs before evaluation. |
| **R2** | **External Maze Package Integration Failure**<br>The evaluator reinstalls the original wheel, exposing unhandled bugs or reliance on internal modifications. | Medium | Critical | Strictly treat `mazegenerator` as a read-only black box. Build a dedicated `MazeAdapter` class. Never modify the wheel file. |
| **R3** | **Type Checking & Flake8 Violations**<br>Late accumulation of `mypy` and `flake8` errors that become overwhelming to fix on the last day. | High | High | Run `make lint` on every commit/PR from Day 1. Use type annotations (`typing`) on all functions and variables as they are written. |
| **R4** | **Packaging / Itch.io Issues**<br>Standalone executable crashes on other machines or fails to upload to Itch.io at the deadline. | Medium | High | Attempt a draft packaging build early (Day 11–12) rather than waiting for the final day. Test on a clean environment. |
| **R5** | **Ghost AI Performance / Wall Clipping**<br>Ghosts get stuck in walls, loop endlessly, or cause frame drops due to inefficient path calculations. | Medium | Medium | Use simple Manhattan distance heuristic or BFS on intersections only, rather than full recalculations every pixel frame. |
