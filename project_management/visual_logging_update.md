# Returning eyes, result gardens and persistent diagnostics

Recorded on 2026-11-02 for team members mal-jama and mewaysi.

## Changes and integration

- Eaten ghosts become harmless eyes and follow shortest existing maze passages
  to their own corner. Captures preserve the actor's continuous edge position;
  rewards occur once. Eyes wait for the configured cooldown before restoring
  their body. Normal chase/flee policy and base speed 1.5 remain unchanged.
- Return travel adapts to route length so supported boards normally reach home
  before the configured 5–10 second cooldown ends. G freezes eye motion while
  the cooldown advances; a remote eye cannot reactivate until it reaches home.
  Pause freezes everything. Life loss preserves harmless returns; new levels
  and runs create fresh ghosts and new home-distance maps.
- Victory uses a golden garden, trophy and drifting leaves. Game Over uses a
  moonlit indigo garden, light rain and resting arcade badge. Cached scenery
  and a monotonic decorative clock leave gameplay and its RNG untouched.
  Score, name validation, Backspace, Enter and Esc retain their existing flow.
- ErrorLogSession opens errors.log in XDG user data before configuration is
  loaded. UTC records retain module, severity and full exception tracebacks;
  console messages stay brief. Rotation keeps three 1 MiB backups. An unusable
  file sink falls back to console and produces a menu/end-screen warning.
  Startup/runtime paths release the window and owned logging resources.
  A configuration occupying the log or a backup path is preserved by choosing
  a non-conflicting diagnostic filename before opening any file handler.

Distinct per-ghost personalities were explicitly excluded. The assigned wheel,
generator adapter, active ghost AI, configuration, life carry-over, level time
limits and highscore format are unchanged. The existing reference project was
used read-only and was not modified.

## Executed checks

The complete suite passed **210 tests in 6.23 seconds**. Flake8 and both the
required mypy flags and strict mypy passed, checking 27 Python files. New tests
cover edge continuity, legal returns, harmlessness, single capture rewards,
home waiting, pause/G behavior, level/run resets, frame partitions, dimensions
15/20/35 and cooldowns 5/7/10 seconds. Graphics tests inspect actual frames and
text bounds at 1000x850 and 640x544. Logging tests cover rotation, traceback
separation, handler restoration, failed opens/writes/rollovers and UI/launcher
recovery.

Real source-entry diagnostics passed for ordinary and commented configurations:
returning eyes, home waiting, a real first-level clear, ten-level Victory,
timeout Game Over, name/save/reload and menu reuse. Missing arguments/config,
missing dependencies and an invalid display driver returned the expected
status with a short console message and persistent diagnostic details.

Actual screenshots in [screenshots/](screenshots/) include returning eyes,
waiting home eyes, Victory and Game Over. Screens were produced by the real
frontend with SDL dummy, not a human playthrough. See
[finish_performance.json](finish_performance.json) for 150 warm frames per
screen at each viewport. Warm means were 2.9–5.4 ms, with p95 below 6.6 ms.
Initial cached-scene construction was measured separately at 62–185 ms.

Packaging and current archive results are recorded in
[final_verification.json](final_verification.json) and
[release_check.json](release_check.json). Native desktop peer review and
platform publication remain unclaimed manual checks.
