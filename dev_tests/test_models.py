"""Exercise real-maze gameplay without drawing callbacks or wall-clock time."""

from dataclasses import replace
import math
from typing import cast

import pytest

from pacman.configuration import GameConfig, LevelConfig
from pacman.maze_adapter import Cell, Direction
from pacman.models import Actor, Game, State


@pytest.fixture
def game() -> Game:
    """Create an isolated first level with the assigned real generator."""
    model = Game(GameConfig())
    model.start()
    model.cheats.frozen = True
    return model


def direction_between(start: Cell, end: Cell) -> Direction:
    """Identify a single orthogonal graph edge's movement direction."""
    delta = (end[0] - start[0], end[1] - start[1])
    return next(item for item in Direction if item.delta == delta)


def test_distribution(game: Game) -> None:
    """Cover most eligible corridors with distinct, reachable collectibles."""
    reserved = {game.maze.spawn, *game.maze.ghost_spawns, *game.powers}
    eligible = game.maze.reachable - reserved
    assert len(game.pellets) == max(42, math.ceil(len(eligible) * .8))
    assert game.pellets <= eligible
    assert len(game.ghosts) == len(game.powers) == 4


def test_real_player_movement(game: Game) -> None:
    """Traverse a legal edge and consume its pellet exactly once."""
    start = game.player.cell
    target = game.maze.neighbors(start)[0]
    game.pellets.add(target)
    game.set_direction(direction_between(start, target))
    game.update(1 / game.config.player_speed)
    assert game.player.cell == target
    assert game.score == game.config.points_per_pacgum
    assert target not in game.pellets


def test_wall_collision(game: Game) -> None:
    """Held movement cannot cross blocked sides or the map boundary."""
    for cell in sorted(game.maze.reachable):
        blocked = [d for d in Direction if game.maze.step(cell, d) is None]
        if blocked:
            game.player.reset(cell)
            game.set_direction(blocked[0])
            game.update(.5)
            assert game.player.cell == cell
            assert game.player.target is None
            return
    pytest.fail("Real maze must have a wall")


def test_buffered_turn_and_reversal(game: Game) -> None:
    """Reverse continuously mid-edge without teleporting or crossing walls."""
    start = game.player.cell
    end = game.maze.neighbors(start)[0]
    direction = direction_between(start, end)
    game.set_direction(direction)
    game.update(.075)
    before = game.player.position()
    opposite = next(d for d in Direction
                    if d.delta == tuple(-v for v in direction.delta))
    game.set_direction(opposite)
    assert game.player.position() == before
    game.update(.075)
    assert game.player.cell == start


def test_power_collection_and_ghost_cooldown(game: Game) -> None:
    """Power awards points, eats a ghost once and respawns after delay."""
    power = next(iter(game.powers))
    game.player.reset(power)
    ghost = game.ghosts[0]
    ghost.reset(power)
    game.update(Game.STEP)
    assert power not in game.powers
    assert game.power_left > 0
    assert not ghost.active
    assert game.score == (game.config.points_per_super_pacgum
                          + game.config.points_per_ghost)
    score = game.score
    game.update(.1)
    assert game.score == score
    game.player.reset(game.maze.spawn)
    game.cheats.frozen = False
    game.cheats.invincible = True
    for other in game.ghosts[1:]:
        other.active = False
        other.respawn_left = 60
    for _ in range(round(game.config.ghost_respawn_delay / Game.STEP)):
        game.update(Game.STEP)
        if ghost.active:
            break
    assert ghost.active and ghost.cell == ghost.home


def test_collision_one_life_respawn_and_invulnerability(game: Game) -> None:
    """Several touching ghosts cost one life and preserve collectibles."""
    pellets = set(game.pellets)
    game.score = 123
    game.invulnerable_left = 0
    for ghost in game.ghosts:
        ghost.reset(game.player.cell)
    game.update(Game.STEP)
    assert game.lives == 2
    assert game.player.cell == game.maze.spawn
    assert game.pellets == pellets and game.score == 123
    for ghost in game.ghosts:
        ghost.reset(game.player.cell)
    game.update(.2)
    assert game.lives == 2


def test_edge_crossing_collision(game: Game) -> None:
    """Actors crossing in opposite directions still collide between centers."""
    start = game.player.cell
    end = game.maze.neighbors(start)[0]
    game.player.target = end
    game.player.progress = .45
    ghost = game.ghosts[0]
    ghost.reset(end)
    ghost.target = start
    ghost.progress = .45
    game.invulnerable_left = 0
    game.update(Game.STEP)
    assert game.lives == 2


def test_pause_freezes_every_timer_and_position(game: Game) -> None:
    """Pause freezes countdown, power, cooldown, boost and immunity."""
    game.power_left = 4
    game.boost_left = 5
    game.ghosts[0].active = False
    game.ghosts[0].respawn_left = 6
    game.pause()
    snapshot = (game.time_left, game.power_left, game.boost_left,
                game.invulnerable_left, game.ghosts[0].respawn_left,
                game.player.position())
    game.update(30)
    assert snapshot == (game.time_left, game.power_left, game.boost_left,
                        game.invulnerable_left, game.ghosts[0].respawn_left,
                        game.player.position())
    game.pause()
    game.update(.1)
    assert game.time_left < snapshot[0]


def test_frame_rate_invariance() -> None:
    """One second of input produces the same result at 30 and 144 FPS."""
    games = [Game(GameConfig()), Game(GameConfig())]
    for model, frames in zip(games, (30, 144)):
        model.start()
        model.cheats.frozen = True
        neighbor = model.maze.neighbors(model.player.cell)[0]
        model.set_direction(direction_between(model.player.cell, neighbor))
        for _ in range(frames):
            model.update(1 / frames)
    assert games[0].player.position() == pytest.approx(
        games[1].player.position())
    assert games[0].time_left == pytest.approx(games[1].time_left)
    assert games[0].score == games[1].score


def test_all_pellets_required_and_progression(game: Game) -> None:
    """Require power pellets too and retain score and lives on next level."""
    game.pellets.clear()
    game.update(Game.STEP)
    assert game.state == State.PLAYING
    game.powers.clear()
    game.score = 777
    game.lives = 2
    game.update(Game.STEP)
    assert cast(State, game.state) == State.TRANSITION
    game.update(1.6)
    assert game.state == State.PLAYING and game.level_index == 1
    assert game.score == 777 and game.lives == 2


def test_first_seed_reproducibility(game: Game) -> None:
    """Restarting restores the fixed first maze and ordinary pellet layout."""
    walls, pellets = game.maze.walls, set(game.pellets)
    game.cheat('f1')
    game.cheat('n')
    game.update(1.6)
    later = game.maze.walls
    game.start()
    assert walls == game.maze.walls and pellets == game.pellets
    assert later != walls


def test_review_skip_all_ten_and_reset(game: Game) -> None:
    """Review tools reach final victory and reset fully on a fresh run."""
    game.cheat('n')
    assert game.level_index == 0 and game.state == State.PLAYING
    game.cheat('f1')
    for index in range(10):
        assert game.level_index == index
        game.cheat('n')
        if index < 9:
            game.update(1.6)
    assert cast(State, game.state) == State.VICTORY
    game.start()
    assert game.lives == 3 and game.score == 0
    assert not game.cheats.enabled and not game.cheats.invincible


def test_review_actions_and_disable(game: Game) -> None:
    """All toggles affect real gameplay and disabling clears sticky effects."""
    game.cheat('f1')
    for key in ('i', 'g', 'l', 'b', 'o'):
        game.cheat(key)
    assert game.cheats.invincible and not game.cheats.frozen
    assert game.lives == 4 and game.boost_left == 10
    assert game.power_left == game.config.power_duration
    game.cheat('f1')
    assert not game.cheats.invincible and not game.cheats.frozen
    assert game.boost_left == 0


def test_game_over_and_timeout(game: Game) -> None:
    """Exhausted lives and expired countdown both produce an explicit loss."""
    game.lives = 1
    game.lose_life()
    assert game.state == State.GAME_OVER and game.lives == 0
    game.start()
    game.time_left = .01
    game.update(.1)
    assert game.state == State.GAME_OVER and 'Time' in game.reason


def test_player_start_even_center() -> None:
    """The protected 42 cannot trap the player on even-sized boards."""
    config = replace(GameConfig(), levels=(LevelConfig(20, 20),) * 10)
    model = Game(config)
    model.start()
    assert model.maze.walls[10][10] == 15
    assert model.player.cell != (10, 10)
    assert model.maze.neighbors(model.player.cell)


def test_actor_interpolation() -> None:
    """Drawing positions interpolate a valid edge without changing topology."""
    actor = Actor((1, 2), target=(2, 2), progress=.25)
    assert actor.position() == (1.25, 2)
    actor.reset((3, 3))
    assert actor.position() == (3, 3)
