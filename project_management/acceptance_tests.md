# Acceptance checks and actual evidence

Date: 2026-10-22. Tests are developer-only programs under `dev_tests/`, separate
from the runtime and excluded from the standalone game archive.

## Executed subsystem checks

The configuration/persistence implementation task executed:

```bash
.venv/bin/python -m pytest dev_tests/test_configuration.py dev_tests/test_highscores.py -q
.venv/bin/flake8 pacman/configuration.py pacman/highscores.py dev_tests/test_configuration.py dev_tests/test_highscores.py
.venv/bin/mypy pacman/configuration.py pacman/highscores.py dev_tests/test_configuration.py dev_tests/test_highscores.py --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

Observed: **95 tests passed**, scoped flake8 exited successfully, and mypy
reported no issues in all four files. Tests include ordinary/commented JSON,
literal hashes, invalid roots/files/encoding, numeric bool/type/range repairs,
ten-level repair, config edits, path traversal and symlink rejection,
name validation, ranking/ties/top-ten truncation, restart persistence,
malformed records, read failures and failed atomic replacement preserving disk.

## Final integration record

The integration owner executed the following checks on the final implementation
and reported their actual outcomes during this session. The build environment
was CPython 3.12.3, PyInstaller 6.22.3, Linux x86_64 and glibc 2.39.

| Gate | Repeatable check | Final result |
| --- | --- | --- |
| Dependency installation | `make install` | PASS |
| Required lint | `make lint` | PASS; exact specified flake8/mypy flags |
| Optional strict lint | `make lint-strict` | PASS; 21 Python files checked |
| All developer tests | `make test` | PASS; 152 tests in 3.42 seconds |
| Source frontend diagnostic | `make run` with diagnostic environment and isolated XDG_DATA_HOME | PASS; ordinary and commented configurations |
| Debug entry point | `make debug`, pdb continue and quit, diagnostic enabled | PASS |
| Missing/extra CLI arguments | Entry point with zero/two config arguments | PASS in application tests; usage/error exit without traceback |
| Display unavailable | Source entry point with unavailable display driver | PASS; readable error, exit 1, no traceback |
| Packaging | `make release` | PASS; approximately 18 MB release/Pacman42-Linux-x86_64.tar.gz |
| Packaged frontend diagnostic | ./run.sh from /tmp with clean env, dummy SDL and fresh XDG data | PASS; 10 levels, 241 first-level collectibles, 2 persisted entries |
| Original inputs unchanged | tools/verify_integrity.py | PASS; original hashes, vendor wheel and installed source/metadata/RECORD |
| Native desktop review | Both team members play with keyboard on a graphical desktop | Not recorded as completed |
| itch.io publication | Upload free unlisted/private archive; verify downloaded launch and actual URL | Manual step remaining |

## Requirement-to-check map

| Requirement | Evidence / review action |
| --- | --- |
| Original generator interface and masks | `test_maze.py`: real wheel, dimensions, masks, reciprocal/open-border validation |
| Reproducibility and later randomness | Maze/model tests compare fixed first seeds and exercise later seed=0 calls |
| Protected `42`, blocked even-size center | `test_maze.py`: 20x20 safe reachable spawn and isolated cell exclusion |
| Four valid corners and distinct items | Maze/model tests inspect corner-region reserves and reachability |
| Motion obeys walls and supports controls | Model movement plus application direction-key tests |
| Pellet/power/ghost scoring | Model set-consumption and inactive-ghost tests |
| Chase/flee | AI distance tests use real topology and legal neighbors |
| Lives, protection and eaten respawn | Model collisions, life loss, cooldown and invulnerability checks |
| Ten levels and final victory | Model progression and full application diagnostic |
| Timer loss and complete pause | Model tests inspect countdown, power, respawn, boost and movement while paused |
| Working cheats and fresh-run reset | Model cheat tests plus F1-assisted diagnostic |
| Menu -> play -> finish -> name -> menu | `test_application.py` and frontend diagnostic |
| Name rules and persistence | 95-test configuration/persistence group above |
| Graphical lifecycle and shutdown | Dummy SDL application tests; repeat starts and quit events |
| Standalone generation and score save | Packaged diagnostic exercised the same real import/model/frontend successfully |

## Manual peer-review route

1. Run normally on a graphical desktop; inspect main-menu scores, instructions
   and keyboard navigation. Start twice across the full flow to verify reuse.
2. Move with arrows and WASD, turn at intersections and test visible walls.
   Inspect the central `42` obstacle and all four ghost/power corner regions.
3. Pause and wait; verify countdown and gameplay states stay frozen. Resume.
   Open Return to Main Menu confirmation, cancel, then confirm on a later try.
4. Enable F1; use O to test edible ghosts, G to inspect their frozen rendering,
   I for safety, B for speed and L for added lives. Disable F1 and start fresh
   to confirm persistent cheat flags reset.
5. Use T to trigger timeout Game Over; enter an invalid name, then a valid one,
   save and restart to verify disk persistence. Test Esc saves as PLAYER.
6. Start again, enable F1 and use N through all ten levels to Victory. Complete
   name entry once and confirm the menu/leaderboard returns without duplicates.
7. Edit a copy of config.json (points, lives, dimensions, timer), relaunch and
   inspect changed behavior. Try a short level list and invalid field types;
   warnings should accompany safe repairs.
8. Extract the standalone archive into a fresh directory and repeat launch,
   movement and score saving. Record OS/glibc and actual platform URL if uploaded.

No native human playthrough, authenticated upload or platform URL is claimed.

## Additional executed integration evidence

The integration owner reports the complete developer suite passed with
**152 tests**, and `make install`, `make run` with both ordinary/commented
configurations, and `make debug` were exercised using the real headless
application flow. Required and strict lint passed. The built standalone launcher
was run from `/tmp` using `env -i` with `PATH=/usr/bin:/bin`, a fresh writable
XDG data directory and SDL's dummy drivers. No development venv/PYTHONPATH was
available to it; it still generated real mazes and completed the full flow.

The diagnostic printed:

```json
{"smoke": "passed", "levels": 10, "first_level_collectibles": 241, "persisted_entries": 2}
```

The distribution is rebuilt after final documentation edits so it contains
the same player guide and notices as the source tree. Normal display-driver
startup failure was also exercised and returned a clear exit-1 message
without a traceback.

[pacing_check.json](pacing_check.json) records an actual traversal of every
default level through real passages without skips. The countdowns were not
extended: their configured limits were 90, 90, 105, 120, 120, 135, 150, 165,
180 and 200 seconds. Observed clear times were respectively 79.0, 78.0, 86.2,
100.8, 98.2, 107.4, 115.4, 126.8, 150.2 and 151.8 seconds, ending in Victory.
The automated player used greedy BFS routes, frozen ghosts and invincibility.
Later mazes were random. This demonstrates a route budget on the recorded
mazes; it does not establish human difficulty balance or every random layout.

Seven actual graphical diagnostic captures are in [screenshots/](screenshots/):
main menu, playing, pause, Victory, Game Over, highscores and instructions.
These were generated from the running frontend, not composed as mockups.

## Final release checks

The rebuilt archive was extracted to a fresh temporary folder. Its entire
installation tree was made read-only, then its launcher ran in two separate
processes with a clean PATH and no venv or PYTHONPATH. Both diagnostics passed;
the second reloaded the first process's scores and left four persisted entries
in writable XDG user data. No installation files were created or modified.
See [release_check.json](release_check.json) for the actual result.

The original wheel was also installed without network access into a new
temporary virtual environment. Importing the application model there generated
a valid real maze with four ghosts and a reachable player start. The working
installation was preserved throughout.

A real X11 launch was attempted using this session's DISPLAY but could not
open the display; it exited clearly with status 1 and no traceback. Graphical
flow and screenshot evidence therefore use SDL's dummy driver. Native human
keyboard play and platform download remain manual checks.

The final persistence review added and passed a regression test that prevents
the active configuration from being overwritten by its highscore filename.
`make clean` was exercised and preserved the source artifacts and releases.

## 2026-11-02 returning eyes, finish scenes and logging

The updated source passes **210 tests in 6.23 seconds**. Flake8 and required
and strict mypy pass for all 27 Python files. Added checks cover harmless legal
eye returns, corner cooldowns, G/pause, life/level/run state, large boards and
frame partitions. Real renderer checks at native/minimum viewport sizes cover
distinct end scenes, repaint, readable names/controls and eye-only rendering.
Logging tests exercise persistent UTC traces, rotation, file failures,
preserved handlers and UI/entry-point recovery.

The source diagnostic now captures returning and waiting eyes before its real
first-level clear and ten-level finish/save/restart flow. Ordinary/commented
configuration diagnostics pass. Usage, missing config/dependency and display
failures produce concise console output and a persistent error record. See
[visual_logging_update.md](visual_logging_update.md) for implementation and
measurement details, and [final_verification.json](final_verification.json)
for the rebuilt archive's current results. Earlier records above retain their
actual historical scope and counts.
