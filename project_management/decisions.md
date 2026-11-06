# Decisions and alternatives

All decisions below were made for this implementation session on 2026-10-22.

| Decision | Reason and alternative |
| --- | --- |
| Keep the assigned wheel unchanged | It is the assignment's mandatory integration contract. Patching its center or replacing its algorithm would break review reinstallation. |
| Use size=(width,height), perfect=False | Actual implementation signature is authoritative; the package quick-start width/height example fails. Loops support chase gameplay. |
| Interpret walls as an immutable graph | BFS and collision checks need topology, not a second generator. A frozen copy and reciprocal checks preserve the source grid. |
| Use the largest reachable component | Isolated mask-15 `42` cells cannot contain actors/items. Keeping a connected play area prevents unreachable completion requirements. |
| Prefer reachable center, then nearest valid center | Geometric center can be blocked on even dimensions. Editing the generator is unnecessary and forbidden. |
| Reserve ghost corners before nearby powers | Both must occupy distinct safe corner-region tiles. Sharing a dangerous ghost start with a power item creates avoidable overlap. |
| Interpret pacgum as a requested minimum | The PDF leaves its meaning open. Mandatory coverage fills most corridors even when the requested count is small. |
| Require both pellet types for completion | The phrase all pacgums is interpreted to include power pellets; this is visible in the HUD and documentation. |
| First level fixed, later seed=0 | This wheel uses zero for fresh randomness. Passing the first seed on every level would repeat layouts. |
| Private Random instances for gameplay | The dependency changes module-global random state. Independent instances keep AI and item-placement state isolated. |
| 120 Hz fixed-step model, 60 FPS presentation | Rules remain independent of drawing cadence and contacts do not depend on one large rendered frame. |
| Timeout ends the run | A clear deterministic loss policy is simpler than regenerating a partially completed level. |
| Initial 2026-10-22 pacing: later levels override a 90-second global timer | Growing mazes need longer routes. A real ten-level no-skip traversal verified the shipped 90,90,105,120,120,135,150,165,180,200-second limits with countdowns unchanged and ghosts frozen. |
| Preserve score/items/countdown after life loss | A contact costs one life, not already earned progress. Active ghosts reset and a 2-second protection window prevents immediate repeated losses. |
| Pause by stopping simulation updates | All gameplay clocks freeze consistently, including respawn and boost, rather than only the visible countdown. |
| pygame behind a limited graphics facade | Linux installation and headless testing are practical; only operations corresponding to MLX window, image, pixel, text and event capabilities are used. |
| Fit the desktop by scaling application coordinates | Query desktop size and adjust pixel coordinates, radii and font sizes before rasterization; no pygame image transform is required. |
| Code-generated game sprites | Avoid external art dependencies and keep maze/entity drawing reproducible. pygame's default text font remains a dependency asset. |
| Repair fields; reject broken whole files | Wrong individual settings recover visibly. Unreadable/invalid JSON cannot reliably describe a configuration and exits with a clear message. |
| Keep at least ten levels and bound the list to 100 | Repairs uphold the mandatory run length while limiting accidental huge configuration arrays. |
| XDG user-data scores by default | Packaged installations may be read-only. Relative source paths remain useful during review; frozen paths redirect to user data. |
| Atomic JSON leaderboard, stable ties | Readable data and same-directory replacement reduce corruption; older equal scores retain precedence. A database would add needless scope. |
| Esc on finish saves PLAYER | This provides a quick explicit completion action without a blank/unusable player name or silently skipping a completed result. |
| Cheats remain leaderboard-eligible | Review mode supports fast end-to-end evaluation. There is one transparent local table, not hidden eligibility rules. |
| Linux folder distribution via PyInstaller | A repeatable standalone build includes Python and the original dependency. A root spec and shell script make rebuilding inspectable. |
| Manual authenticated platform upload | No publisher credentials/connection were available. A local package cannot truthfully be reported as a published game. |

Defense changes should stay small and local: adjust points or timers in config,
coverage logic in `models.py`, chase/flee choices in `ghost_ai.py`, name rules
in `highscores.py` and their UI feedback in `app.py`, or visual colors in
`rendering.py`. The README maps the remaining modules.

On 2026-10-26, the configured level limits and global fallback were doubled
to 180,180,210,240,240,270,300,330,360,400 seconds for a more forgiving run.
Section 6.7 requires a per-level time limit; 90 seconds is an example. The
earlier pacing report is retained with its actual original limits and timings.

On 2026-11-02, eaten ghosts gained continuous, harmless eye travel over the
unchanged maze graph. Each home has one cached BFS distance map; return speed
adapts to the route to fit the existing cooldown. Normal chase/flee decisions
and speed remain unchanged. Bodies reactivate only after home arrival and
cooldown expiry, including when review freeze delays travel. Result gardens
use the same raster facade and independent animation clock. Rotating UTC
diagnostics use XDG user data, with brief console output and a recoverable
file-failure warning. No new ghost personalities were introduced.
