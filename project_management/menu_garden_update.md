# Animated garden menu update

Date: 2026-10-26 (Asia/Amman).

The user requested a clear, smooth, modern animated main-menu background.
The menu now presents an evening garden with a soft moon halo, layered
landscape, swaying willow leaves, drifting clouds, a warm path lantern,
floating fireflies, wind-blown grass/flowers and expanding pond ripples.
Rounded dark green cards preserve keyboard focus and leaderboard legibility.
The four menu actions and top-five score display remain available.

## Implementation and scope

- `pacman/menu_background.py`: independent elapsed-time decorative scene.
  Local deterministic variation does not affect Python's global RNG or AI.
- `pacman/graphics.py`: own clipped polygon/ellipse scanlines, color gradients
  and an opaque image cache capped at eight entries. The scene uses one cached
  background. Failed cache painters restore the active frame correctly.
- `pacman/rendering.py`: main-menu composition and rounded navigation cards.
- Existing MLX-equivalent buffer/image operations are retained; no pygame
  draw, transform, shader, audio, engine or new external artwork is used.
- Gameplay, timers, configuration, highscores and the assigned generator were
  left unchanged. Documentation and the standalone release were updated.

The animation uses monotonic elapsed time rather than advancing the game.
Static scenery is rasterized once. Only moving details are redrawn each frame.
The app's normal loop remains capped at 60 FPS.

## Actual validation

- `make test`: 152 passed in 1.80 seconds.
- `make lint-strict`: flake8 passed; strict mypy passed on 22 Python files.
- Full five-score tables, including 10-character names, were visually inspected
  at 1000x850 and 640x544, at two animation phases and menu selections.
- The global RNG state was unchanged after rendering both scene sizes.
- Warm-cache, 150-frame SDL dummy measurements:

| Viewport | Mean draw time | 95th percentile | Cached backgrounds |
| --- | --- | --- | --- |
| 1000x850 | 10.99 ms | 14.44 ms | 1 |
| 640x544 | 6.83 ms | 8.68 ms | 1 |

These are actual draw measurements on the development host, not a guarantee
for every desktop/compositor. Native human interaction was not claimed.

[Measurement data](garden_menu_performance.json) and
[actual captures](screenshots/garden-menu/) are retained. Representative
[full-size menu](screenshots/garden-menu/1000x850-phase-0.png) and
[small-screen selection](screenshots/garden-menu/640x544-phase-5.png) show
legible content over the live garden.

The release diagnostic and integrity outcomes are recorded in
[final_verification.json](final_verification.json) after rebuilding.
Platform publication remains an external manual step as previously recorded.
