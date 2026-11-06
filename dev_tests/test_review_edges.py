"""Probe gameplay and native-input edge cases through the real integration."""

from dataclasses import replace
import os
from pathlib import Path
from typing import cast

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pacman.app import App  # noqa: E402
from pacman.configuration import GameConfig  # noqa: E402
from pacman.graphics import Graphics  # noqa: E402
from pacman.highscores import HighScoreStore  # noqa: E402
from pacman.maze_adapter import Cell, Direction  # noqa: E402
from pacman.models import Game, State  # noqa: E402


@pytest.fixture
def review_game() -> Game:
    """Prepare a real maze with stationary ghosts and slow precise movement."""
    model = Game(replace(GameConfig(), player_speed=1.0))
    model.start()
    model.cheats.frozen = True
    model.invulnerable_left = 60.0
    return model


def _direction(start: Cell, end: Cell) -> Direction:
    """Translate an observed legal edge into the corresponding key input."""
    delta = (end[0] - start[0], end[1] - start[1])
    return next(direction for direction in Direction
                if direction.delta == delta)


def test_two_reversals_preserve_continuous_position(
    review_game: Game,
) -> None:
    """Rapid opposite inputs reverse velocity without a position jump."""
    model = review_game
    start = model.player.cell
    end = model.maze.neighbors(start)[0]
    forward = _direction(start, end)
    reverse = _direction(end, start)
    model.set_direction(forward)
    model.update(.25)
    quarter = model.player.position()
    model.set_direction(reverse)
    assert model.player.position() == pytest.approx(quarter)
    model.update(.125)
    eighth = model.player.position()
    model.set_direction(forward)
    assert model.player.position() == pytest.approx(eighth)
    model.update(.125)
    assert model.player.position() == pytest.approx(quarter)
    model.update(.75)
    assert model.player.cell == end


def test_blocked_queued_turn_waits_for_later_junction(
    review_game: Game,
) -> None:
    """A premature side input survives one blocked junction and turns later."""
    model = review_game
    for start in sorted(model.maze.reachable):
        for direction in Direction:
            middle = model.maze.step(start, direction)
            end = model.maze.step(middle, direction) if middle else None
            if middle is None or end is None:
                continue
            dx, dy = direction.delta
            for side in Direction:
                sx, sy = side.delta
                if dx * sx + dy * sy != 0:
                    continue
                turn = model.maze.step(end, side)
                if model.maze.step(middle, side) is None and turn:
                    model.player.reset(start)
                    model.set_direction(direction)
                    model.update(.5)
                    model.set_direction(side)
                    model.update(1.5)
                    assert model.player.cell == end
                    model.update(.5)
                    assert model.player.target == turn
                    ex, ey = end
                    tx, ty = turn
                    assert model.player.position() == pytest.approx(
                        ((ex + tx) / 2, (ey + ty) / 2)
                    )
                    return
    pytest.fail("The assigned real maze should contain a delayed side turn")


@pytest.mark.parametrize("frightened", [False, True])
def test_real_ghost_targets_chase_or_flee(
    review_game: Game, frightened: bool,
) -> None:
    """Actual ghost movement chooses a near or distant reachable neighbor."""
    model = review_game
    distances = model.maze.distances(model.player.cell)
    for cell in sorted(model.maze.reachable):
        options = model.maze.neighbors(cell)
        values = [distances[neighbor] for neighbor in options]
        if distances[cell] >= 4 and len(set(values)) >= 2:
            ghost = model.ghosts[0]
            ghost.reset(cell)
            for other in model.ghosts[1:]:
                other.active = False
                other.respawn_left = 60.0
            model.cheats.frozen = False
            model.power_left = 10 if frightened else 0
            model.update(Game.STEP)
            assert ghost.target in options
            assert ghost.target is not None
            target_distance = distances[ghost.target]
            expected = max(values) if frightened else min(values)
            assert target_distance == expected
            assert ghost.position() != tuple(map(float, cell))
            return
    pytest.fail("The assigned real maze should have a chase/flee junction")


def test_invincibility_protects_last_life_and_forced_loss_still_works(
    review_game: Game,
) -> None:
    """Dangerous contact cannot end an invincible run; K can test Game Over."""
    model = review_game
    model.lives = 1
    model.invulnerable_left = 0
    model.cheat("f1")
    model.cheat("i")
    for ghost in model.ghosts:
        ghost.reset(model.player.cell)
    model.update(Game.STEP)
    assert model.lives == 1 and model.state == State.PLAYING
    model.cheat("k")
    assert model.lives == 0 and cast(State, model.state) == State.GAME_OVER


def test_powered_home_overlap_respawn_rewards_only_one_consumption(
    review_game: Game,
) -> None:
    """A ghost returning onto a powered player is eaten once per cooldown."""
    model = review_game
    ghost = model.ghosts[0]
    ghost.active = False
    ghost.respawn_left = Game.STEP / 2
    model.player.reset(ghost.home)
    model.power_left = 10
    before = model.score
    model.update(Game.STEP)
    assert not ghost.active
    assert model.score == before + model.config.points_per_ghost
    model.update(.25)
    assert model.score == before + model.config.points_per_ghost
    assert ghost.respawn_left > model.config.ghost_respawn_delay - .3
    assert model.lives == model.config.lives


def test_repeated_skip_cannot_queue_multiple_transitions(
    review_game: Game,
) -> None:
    """Repeated N during the cleared overlay progresses exactly one level."""
    model = review_game
    model.cheat("f1")
    model.cheat("n")
    assert model.state == State.TRANSITION
    model.update(.75)
    transition_left = model.transition_left
    for _ in range(30):
        model.cheat("n")
    assert model.level_index == 0
    assert model.transition_left == transition_left
    model.update(.8)
    assert model.level_index == 1 and cast(State, model.state) == State.PLAYING
    model.update(.1)
    assert model.level_index == 1


def test_fractional_frame_sizes_preserve_all_gameplay_timers() -> None:
    """Uneven frame partitions preserve countdown, effects and respawn time."""
    large = Game(GameConfig())
    small = Game(GameConfig())
    for model in (large, small):
        model.start()
        model.cheats.frozen = True
        model.power_left = 3.0
        model.boost_left = 4.0
        model.invulnerable_left = 5.0
        model.ghosts[0].active = False
        model.ghosts[0].respawn_left = 6.0
    large.update(.913)
    for _ in range(91):
        small.update(.01)
    small.update(.003)
    assert (
        large.time_left, large.power_left, large.boost_left,
        large.invulnerable_left, large.ghosts[0].respawn_left,
    ) == pytest.approx((
        small.time_left, small.power_left, small.boost_left,
        small.invulnerable_left, small.ghosts[0].respawn_left,
    ))


def test_native_keys_and_text_do_not_duplicate_name_characters() -> None:
    """Combine native key and text events without duplicating typed letters."""
    import pygame

    graphics = Graphics()
    try:
        pygame.event.clear()
        for key in (pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE,
                    pygame.K_UP, pygame.K_F1):
            pygame.event.post(pygame.event.Event(
                pygame.KEYDOWN, key=key, unicode="",
            ))
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_a, unicode="A",
        ))
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text="A"))
        events = graphics.events()
        keys = [event.key for event in events if event.kind == "key"]
        assert keys == ["enter", "space", "escape", "up", "f1", "a"]
        assert [event.text for event in events if event.kind == "text"] == [
            "A",
        ]
    finally:
        graphics.close()


def test_finishing_cheat_does_not_type_its_key_into_name(
    tmp_path: Path,
) -> None:
    """The final N key's matching native text event is consumed as gameplay."""
    import pygame

    app = App(GameConfig(), HighScoreStore(tmp_path / "scores.json"))
    try:
        app.start()
        app.game.level_index = len(app.game.config.levels) - 1
        app.game.cheat("f1")
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_n, unicode="n",
        ))
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text="n"))
        for event in app.graphics.events():
            app.handle(event)
        assert app.game.state == State.VICTORY
        assert app.name == ""
    finally:
        app.graphics.close()
