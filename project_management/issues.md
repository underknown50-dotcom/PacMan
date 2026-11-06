# Issues, fixes and release blockers

Date: 2026-10-22.

## Resolved by implementation

| Issue found | Resolution |
| --- | --- |
| Bundled quick-start constructor uses unsupported width/height keywords | Adapter calls the actual size tuple API. |
| Exact center can be a mask-15 cell on even dimensions | Choose the nearest reachable center tile without touching the generator. |
| Corner ghosts and power pellets would overlap on exact corners | Reserve four corner ghost starts, then four distinct nearest valid power cells. |
| Generator resets global RNG state | Give AI and pellet placement private Random instances. |
| A short config could accidentally expose fewer than ten levels | Repair/pad and warn; accept at most 100 levels. |
| Bool is an int subclass in Python | Explicitly reject booleans in numeric config and leaderboard validation. |
| Comment stripping could damage literal hashes | Remove only whole lines whose first non-whitespace character is #. |
| Read-only packaged asset directories cannot store scores | Use XDG user data and redirect frozen relative score paths. |
| A failed write could truncate the leaderboard | Temp file, flush/fsync, atomic replacement; keep memory and old disk on error. |
| Equal scores could reorder unpredictably | Stable descending ranking preserves older ties. |
| Multiple contacts could consume several lives at once | Resolve one loss, reset actors and apply 2 seconds of protection. |
| An eaten ghost could be rewarded repeatedly | Mark inactive immediately and restore only after its respawn timer. |
| Pausing just the HUD timer would leave cooldowns active | Stop all model simulation updates while paused. |
| Finished-screen Esc might silently lose a completed result | Explicitly save under PLAYER, then return to menu once. |
| Initial own-file style check found lines over 79 columns | Wrapped implementation/test lines; rerun scoped flake8 and mypy succeeded. |
| Large later mazes could exceed a uniform 90-second route budget | Shipped later-level timer overrides added; actual all-level traversal passed with unchanged countdowns, ghosts frozen and invincibility. |
| A 1000x850 physical window could exceed a smaller desktop | Desktop query and application coordinate/radius/font scaling added without image transforms. |
| Strict mypy assumed model enum state stayed narrowed across mutating method calls | Explicit state casts make the mutation boundary clear; optional strict lint now passes. |
| A score filename could resolve to its active config | Reject that destination and warn/default to user data; regression test passes. |
| The N key text could leak into the Victory name field | Suppress the completing command's trailing text event while accepting fresh name input. |
| Floating-point remainder could delay a 1.5-second transition by a tick | Use a small tolerance consistent with countdown and respawn timers. |

## Outstanding release actions and limits

| Item | Owner / status |
| --- | --- |
| Native desktop keyboard/visual review and peer discussion | Both team members; no completed playthrough is recorded |
| Free unlisted/private itch.io upload and verified URL | mal-jama leads release; both verify the downloaded build |
| Broader OS/glibc compatibility | Current release targets Linux x86_64; rebuild/test additional targets explicitly |
| Simultaneous writers | Atomic saves are not merged; last writer wins |

The platform upload remains a mandatory external submission gate. A complete
local build and clear instructions do not count as publication. No passwords
or secret credentials are needed in this repository or chat.

No team conflict has been reported. New integration defects should be recorded
with their concrete trigger, affected module, current investigation lead, fix
and the actual repeated check. Study and defense responsibilities follow
[PACMAN_TEAM_PARTS.md](../PACMAN_TEAM_PARTS.md).
