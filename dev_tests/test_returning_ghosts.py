"""Verify harmless returning eyes against real maze topology and timers."""

from dataclasses import replace
import math

import pytest

from pacman.configuration import GameConfig, LevelConfig
from pacman.maze_adapter import Cell, Direction
from pacman.models import Game, Ghost, State


def _game(width: int = 20, delay: float = 7.0) -> Game:
    """Prepare a real maze and keep unrelated ghosts harmless during checks."""
    config = replace(
        GameConfig(), ghost_respawn_delay=delay,
        levels=(LevelConfig(width, width, 3600.0),) * 10,
    )
    model = Game(config)
    model.start()
    model.invulnerable_left = 0.0
    for ghost in model.ghosts:
        ghost.active = False
        ghost.respawn_left = 3600.0
    return model


def _far_from_home(model: Game, ghost: Ghost) -> Cell:
    """Find a distant valid capture position for a specific home corner."""
    distances = model.maze.distances(ghost.home)
    return max(distances, key=lambda cell: (distances[cell], cell))


def _capture_at(model: Game, ghost: Ghost, cell: Cell) -> None:
    """Capture an active ghost without relocating the player or items."""
    ghost.reset(cell)
    ghost.active = True
    model._eat_ghost(ghost)


def _assert_on_graph(model: Game, ghost: Ghost) -> None:
    """Ensure an eye actor occupies a legal cell or reciprocal graph edge."""
    assert ghost.cell in model.maze.reachable
    assert 0.0 <= ghost.progress < 1.0
    if ghost.target is not None:
        assert ghost.target in model.maze.neighbors(ghost.cell)
        assert ghost.cell in model.maze.neighbors(ghost.target)


@pytest.mark.parametrize("progress", [.2, .8])
@pytest.mark.parametrize("heading_home", [False, True])
def test_mid_edge_capture_preserves_continuous_position(
    progress: float, heading_home: bool,
) -> None:
    """Capture may reverse travel without jumping from the existing edge."""
    model = _game()
    ghost = model.ghosts[0]
    distances = model.maze.distances(ghost.home)
    far = _far_from_home(model, ghost)
    near = min(model.maze.neighbors(far), key=distances.__getitem__)
    start, end = (far, near) if heading_home else (near, far)
    ghost.reset(start)
    ghost.active = True
    ghost.target = end
    ghost.progress = progress
    delta = (end[0] - start[0], end[1] - start[1])
    ghost.direction = next(d for d in Direction if d.delta == delta)
    position = ghost.position()
    model._eat_ghost(ghost)
    assert ghost.position() == pytest.approx(position)
    assert not ghost.active and ghost.returning
    assert ghost.return_speed >= 6.0
    _assert_on_graph(model, ghost)
    model.update(Game.STEP)
    assert ghost.position() != pytest.approx(position)
    assert math.dist(position, ghost.position()) <= (
        ghost.return_speed * Game.STEP + 1e-9
    )
    _assert_on_graph(model, ghost)


@pytest.mark.parametrize("ghost_index", range(4))
def test_return_follows_shortest_legal_passages_to_its_own_corner(
    ghost_index: int,
) -> None:
    """Every sampled return edge is legal, continuous and closer to home."""
    model = _game()
    ghost = model.ghosts[ghost_index]
    distances = model.maze.distances(ghost.home)
    _capture_at(model, ghost, _far_from_home(model, ghost))
    before_distance = float(distances[ghost.cell])
    for _ in range(math.ceil(model.config.ghost_respawn_delay / Game.STEP)):
        old_position = ghost.position()
        speed = ghost.return_speed
        model.update(Game.STEP)
        _assert_on_graph(model, ghost)
        assert math.dist(old_position, ghost.position()) <= (
            speed * Game.STEP + 1e-8
        )
        remaining = float(distances[ghost.cell])
        if ghost.target is not None:
            remaining = min(
                ghost.progress + distances[ghost.cell],
                1.0 - ghost.progress + distances[ghost.target],
            )
        assert remaining <= before_distance + 1e-9
        before_distance = remaining
        if not ghost.returning:
            break
    else:
        pytest.fail("Returning eyes did not reach their assigned corner")
    assert ghost.cell == ghost.home
    assert ghost.target is None and ghost.progress == 0.0
    assert not ghost.active and ghost.respawn_left > .70
    assert ghost.return_speed == 0.0


def test_returning_and_waiting_eyes_are_harmless_and_rewarded_once() -> None:
    """Touching inactive eyes cannot cost lives or award additional points."""
    model = _game()
    ghost = model.ghosts[0]
    neighbor = model.maze.neighbors(ghost.home)[0]
    _capture_at(model, ghost, neighbor)
    awarded = model.config.points_per_ghost
    assert model.score == awarded
    for power in (0.0, 5.0):
        model.power_left = power
        model.player.reset(ghost.cell)
        model._collisions()
        model._eat_ghost(ghost)
        assert model.lives == model.config.lives
        assert model.score == awarded
    model.player.reset(model.maze.spawn)
    model.update(.25)
    assert ghost.cell == ghost.home
    assert not ghost.active and not ghost.returning
    for power in (0.0, 5.0):
        model.power_left = power
        model.player.reset(ghost.home)
        model._collisions()
        assert model.lives == model.config.lives
        assert model.score == awarded


def test_early_home_arrival_waits_for_the_full_cooldown() -> None:
    """A short route cannot restore the body before the configured delay."""
    model = _game()
    ghost = model.ghosts[0]
    _capture_at(model, ghost, model.maze.neighbors(ghost.home)[0])
    model.update(.25)
    assert ghost.cell == ghost.home and ghost.target is None
    assert not ghost.returning and not ghost.active
    model.update(model.config.ghost_respawn_delay - .25 - 2 * Game.STEP)
    assert ghost.cell == ghost.home and not ghost.active
    assert ghost.respawn_left == pytest.approx(2 * Game.STEP)
    model.update(2 * Game.STEP)
    assert ghost.active and not ghost.returning
    assert ghost.cell == ghost.home and ghost.target is None
    assert ghost.respawn_left == 0.0
    assert model.score == model.config.points_per_ghost


def test_freeze_holds_remote_eyes_until_return_travel_resumes() -> None:
    """G stops eye motion while cooldown continues without a remote respawn."""
    model = _game()
    ghost = model.ghosts[0]
    _capture_at(model, ghost, _far_from_home(model, ghost))
    model.cheat("f1")
    model.cheat("g")
    snapshot = (ghost.cell, ghost.target, ghost.progress, ghost.position())
    model.update(model.config.ghost_respawn_delay + .5)
    assert snapshot == (
        ghost.cell, ghost.target, ghost.progress, ghost.position(),
    )
    assert ghost.returning and not ghost.active
    assert ghost.cell != ghost.home and ghost.respawn_left == 0.0
    assert model.score == model.config.points_per_ghost
    model.cheat("g")
    model.update(Game.STEP)
    assert ghost.position() != snapshot[-1]
    assert not ghost.active and ghost.returning
    for _ in range(math.ceil(model.config.ghost_respawn_delay / Game.STEP)):
        model.update(Game.STEP)
        if ghost.active:
            assert not ghost.returning
            assert ghost.cell == ghost.home and ghost.target is None
            break
    else:
        pytest.fail("Expired returning eyes did not reactivate at home")


def test_pause_freezes_return_travel_and_every_associated_timer() -> None:
    """Pause freezes eye progress and cooldown together with global effects."""
    model = _game()
    ghost = model.ghosts[0]
    _capture_at(model, ghost, _far_from_home(model, ghost))
    model.power_left = 4.0
    model.boost_left = 5.0
    model.update(.2)
    model.pause()
    snapshot = (
        ghost.cell, ghost.target, ghost.progress, ghost.position(),
        ghost.respawn_left, ghost.return_speed, model.time_left,
        model.power_left, model.boost_left, model.invulnerable_left,
    )
    model.update(30.0)
    assert snapshot == (
        ghost.cell, ghost.target, ghost.progress, ghost.position(),
        ghost.respawn_left, ghost.return_speed, model.time_left,
        model.power_left, model.boost_left, model.invulnerable_left,
    )
    model.pause()
    model.update(.1)
    assert ghost.position() != snapshot[3]
    assert ghost.respawn_left < snapshot[4]
    assert model.time_left < snapshot[6]


def test_new_run_removes_every_returning_and_waiting_state() -> None:
    """Restart creates four fresh normal ghosts and discards all cooldowns."""
    model = _game()
    walls = model.maze.walls
    for ghost in model.ghosts:
        _capture_at(model, ghost, _far_from_home(model, ghost))
    assert model.score == 4 * model.config.points_per_ghost
    model.cheat("f1")
    model.cheat("g")
    old_ghosts = tuple(model.ghosts)
    model.start()
    assert model.state == State.PLAYING
    assert model.score == 0 and model.lives == model.config.lives
    assert model.maze.walls == walls
    assert not model.cheats.enabled and not model.cheats.frozen
    for ghost in model.ghosts:
        assert all(ghost is not previous for previous in old_ghosts)
        assert ghost.active and not ghost.returning
        assert ghost.cell == ghost.home and ghost.target is None
        assert ghost.respawn_left == ghost.return_speed == 0.0


def test_life_loss_preserves_harmless_return_progress() -> None:
    """Player respawn cannot teleport eyes or restore an inactive body."""
    model = _game()
    ghost = model.ghosts[0]
    _capture_at(model, ghost, _far_from_home(model, ghost))
    model.update(.2)
    snapshot = (ghost.cell, ghost.target, ghost.progress, ghost.respawn_left)
    position = ghost.position()
    model.lose_life()
    assert model.lives == model.config.lives - 1
    assert model.score == model.config.points_per_ghost
    assert snapshot == (
        ghost.cell, ghost.target, ghost.progress, ghost.respawn_left,
    )
    assert not ghost.active and ghost.returning
    model.update(Game.STEP)
    assert ghost.position() != position


def test_level_transition_discards_old_return_routes() -> None:
    """A fresh maze clears eye state while retaining earned score/lives."""
    model = _game()
    _capture_at(model, model.ghosts[0],
                _far_from_home(model, model.ghosts[0]))
    model.lives = 2
    old_ghosts = tuple(model.ghosts)
    model.complete_level()
    model.update(1.5)
    assert model.state == State.PLAYING and model.level_index == 1
    assert model.score == model.config.points_per_ghost and model.lives == 2
    for ghost in model.ghosts:
        assert all(ghost is not previous for previous in old_ghosts)
        assert ghost.active and not ghost.returning
        assert ghost.cell == ghost.home and ghost.target is None
        assert ghost.respawn_left == ghost.return_speed == 0.0


@pytest.mark.parametrize("width", [15, 20, 35])
@pytest.mark.parametrize("delay", [5.0, 7.0, 10.0])
def test_long_routes_arrive_before_cooldown_on_supported_boards(
    width: int, delay: float,
) -> None:
    """Adaptive harmless-eye speed retains the configured respawn deadline."""
    model = _game(width, delay)
    ghost = model.ghosts[0]
    _capture_at(model, ghost, _far_from_home(model, ghost))
    elapsed = 0.0
    while ghost.returning and elapsed <= delay:
        model.update(Game.STEP)
        elapsed += Game.STEP
    assert not ghost.returning and not ghost.active
    assert ghost.cell == ghost.home
    assert elapsed <= delay - .75 + Game.STEP + 1e-8
    assert ghost.respawn_left >= .75 - Game.STEP - 1e-8


def test_return_motion_and_cooldown_are_frame_partition_independent() -> None:
    """Unequal frame partitions produce the same edge progress and timers."""
    large = _game()
    small = _game()
    for model in (large, small):
        ghost = model.ghosts[0]
        _capture_at(model, ghost, _far_from_home(model, ghost))
        model.power_left = 3.0
    large.update(.913)
    for _ in range(91):
        small.update(.01)
    small.update(.003)
    left, right = large.ghosts[0], small.ghosts[0]
    assert left.cell == right.cell and left.target == right.target
    assert left.active == right.active and left.returning == right.returning
    assert left.position() == pytest.approx(right.position())
    assert left.progress == pytest.approx(right.progress)
    assert left.respawn_left == pytest.approx(right.respawn_left)
    assert large.time_left == pytest.approx(small.time_left)
    assert large.power_left == pytest.approx(small.power_left)
