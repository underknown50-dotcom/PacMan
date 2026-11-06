"""Check actual result frames and harmless-eye rendering at both viewports."""

from collections.abc import Iterator
import os
from typing import cast

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

from pacman.configuration import GameConfig  # noqa: E402
from pacman.graphics import Color, Graphics  # noqa: E402
from pacman.models import Game, State  # noqa: E402
from pacman.rendering import Renderer  # noqa: E402


@pytest.fixture(params=((1000, 850), (640, 544)))
def scene(request: pytest.FixtureRequest) -> Iterator[
    tuple[Graphics, Renderer, Game]
]:
    """Use the real SDL pixel facade at native and minimum window sizes."""
    width, height = cast(tuple[int, int], request.param)
    graphics = Graphics()
    graphics.screen = pygame.display.set_mode((width, height))
    graphics._scale = width / graphics.width
    model = Game(GameConfig())
    model.start()
    try:
        yield graphics, Renderer(graphics), model
    finally:
        graphics.close()


def _garden_pixels(graphics: Graphics) -> list[tuple[int, int, int]]:
    """Sample scenery margins away from the title and result-card text."""
    samples: list[tuple[int, int, int]] = []
    for left in (30, 70, 110, 150, 850, 890, 930, 970):
        for top in range(350, 730, 29):
            pixel = graphics.screen.get_at((
                round(left * graphics._scale), round(top * graphics._scale),
            ))
            samples.append((pixel.r, pixel.g, pixel.b))
    return samples


def test_finish_backgrounds_are_distinct_and_repaint_every_frame(
    scene: tuple[Graphics, Renderer, Game], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Different scenery survives repainting over arbitrary previous pixels."""
    graphics, renderer, model = scene
    monkeypatch.setattr("pacman.finish_background.time.monotonic", lambda: 10.)
    model.state = State.VICTORY
    renderer.finish(model, "PLAYER42", "")
    victory = _garden_pixels(graphics)
    victory_frame = pygame.image.tobytes(graphics.screen, "RGB")
    graphics.screen.fill((255, 0, 255))
    renderer.finish(model, "PLAYER42", "")
    assert pygame.image.tobytes(graphics.screen, "RGB") == victory_frame
    model.state = State.GAME_OVER
    model.reason = "Time ran out"
    renderer.finish(model, "PLAYER42", "")
    loss = _garden_pixels(graphics)
    different = sum(first != second for first, second in zip(victory, loss))
    assert different > len(victory) * .8
    channel_difference = sum(
        abs(a - b)
        for first, second in zip(victory, loss)
        for a, b in zip(first, second)
    ) / (len(victory) * 3)
    assert channel_difference > 15
    assert len(graphics._layers) == 2


def test_finish_presentation_does_not_change_gameplay(
    scene: tuple[Graphics, Renderer, Game], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Result frames cannot advance gameplay timers, collectibles or RNG."""
    _, renderer, model = scene
    model.state = State.GAME_OVER
    model.time_left = 123.4
    model.power_left = 4.2
    model.boost_left = 3.1
    model.transition_left = .8
    model.ghosts[0].active = False
    model.ghosts[0].returning = True
    model.ghosts[0].respawn_left = 6.3

    def snapshot() -> tuple[object, ...]:
        """Capture observable run state rather than renderer internals."""
        return (
            model.state, model.score, model.lives, model.level_index,
            model.time_left, model.power_left, model.invulnerable_left,
            model.boost_left, model.transition_left, model.player.position(),
            tuple((ghost.position(), ghost.cell, ghost.target, ghost.progress,
                   ghost.active, ghost.returning, ghost.respawn_left)
                  for ghost in model.ghosts),
            frozenset(model.pellets), frozenset(model.powers),
            model.rng.getstate(),
        )

    before = snapshot()
    for now in (100., 102.5, 119.):
        monkeypatch.setattr("pacman.finish_background.time.monotonic",
                            lambda: now)
        renderer.finish(model, "PLAYER", "Enter a name before saving.")
    assert snapshot() == before


def test_inactive_ghosts_draw_interpolated_eyes_without_bodies(
    scene: tuple[Graphics, Renderer, Game], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Draw moving and waiting harmless ghosts through the eye facade."""
    graphics, renderer, model = scene
    eyes: list[tuple[int, int]] = []
    bodies: list[tuple[int, int]] = []
    original_eyes = graphics.eyes
    original_ghost = graphics.ghost

    def record_eyes(
        cx: int, cy: int, radius: int, direction: str = "LEFT",
    ) -> None:
        """Record drawing positions while preserving the real eye pixels."""
        eyes.append((cx, cy))
        original_eyes(cx, cy, radius, direction)

    def record_body(
        cx: int, cy: int, radius: int, color: Color,
        direction: str = "LEFT", frightened: bool = False, phase: int = 0,
    ) -> None:
        """Detect an incorrect dangerous body drawn for an inactive ghost."""
        bodies.append((cx, cy))
        original_ghost(cx, cy, radius, color, direction, frightened, phase)

    monkeypatch.setattr(graphics, "eyes", record_eyes)
    monkeypatch.setattr(graphics, "ghost", record_body)
    for ghost in model.ghosts:
        ghost.active = False
    moving = model.ghosts[0]
    moving.cell = model.maze.spawn
    moving.target = model.maze.neighbors(moving.cell)[0]
    moving.returning = True
    positions: list[tuple[int, int]] = []
    for progress in (0., .5, 1.):
        moving.progress = progress
        eyes.clear()
        renderer.game(model)
        assert len(eyes) == 4
        positions.append(eyes[0])
    assert not bodies
    assert positions[0] != positions[2]
    expected = tuple((a + b) / 2
                     for a, b in zip(positions[0], positions[2]))
    assert positions[1] == pytest.approx(expected, abs=1)
    cx, cy = positions[2]
    center_x = round(cx * graphics._scale)
    center_y = round(cy * graphics._scale)
    nearby = [
        graphics.screen.get_at((center_x + dx, center_y + dy))
        for dx in range(-6, 7) for dy in range(-6, 7)
    ]
    assert any(pixel.r >= 225 and pixel.g >= 225 and pixel.b >= 225
               for pixel in nearby)


def test_finish_name_feedback_and_controls_fit_the_window(
    scene: tuple[Graphics, Renderer, Game], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Measure actual text to keep maximum names and save hints readable."""
    graphics, renderer, model = scene
    rendered: list[str] = []
    original_text = graphics.text

    def inspect_text(
        text: str, x: int, y: int, size: int = 22,
        color: Color = (231, 237, 251), center: bool = False,
    ) -> None:
        """Check the font-image bounds after the adapter draws the text."""
        original_text(text, x, y, size, color, center)
        font_size = max(10, round(size * graphics._scale))
        width, height = graphics._fonts[font_size].size(text)
        left = round(x * graphics._scale) - (width // 2 if center else 0)
        top = round(y * graphics._scale)
        assert 0 <= left <= graphics.screen.get_width() - width
        assert 0 <= top <= graphics.screen.get_height() - height
        rendered.append(text)

    monkeypatch.setattr(graphics, "text", inspect_text)
    model.score = 12345678901
    for state in (State.VICTORY, State.GAME_OVER):
        model.state = state
        renderer.finish(model, "WWWWWWWWWW",
                        "Names have at most 10 characters.")
    assert any("WWWWWWWWWW" in text for text in rendered)
    assert "Names have at most 10 characters." in rendered
    assert any("ENTER Save" in text and "ESC Save as PLAYER" in text
               for text in rendered)
