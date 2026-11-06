"""Deterministic, graphics-independent actors, rules and run state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import random

from pacman.cheats import Cheats
from pacman.configuration import GameConfig
from pacman.ghost_ai import calculate_ghost_target, choose_step
from pacman.maze_adapter import Cell, Direction, Maze


class State(str, Enum):
    """Represent the run lifecycle without coupling it to menu rendering."""

    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    TRANSITION = "transition"
    GAME_OVER = "game_over"
    VICTORY = "victory"


@dataclass
class Actor:
    """Travel along one validated graph edge with fractional progress."""

    cell: Cell
    target: Cell | None = None
    progress: float = 0.0
    direction: Direction | None = None

    def position(self) -> tuple[float, float]:
        """Return a continuous cell-center position for drawing/collisions."""
        if self.target is None:
            return float(self.cell[0]), float(self.cell[1])
        return (
            self.cell[0] + (self.target[0] - self.cell[0]) * self.progress,
            self.cell[1] + (self.target[1] - self.cell[1]) * self.progress,
        )

    def reset(self, cell: Cell) -> None:
        """Place an actor safely at a cell without retaining a partial edge."""
        self.cell = cell
        self.target = None
        self.progress = 0.0
        self.direction = None


@dataclass
class Ghost(Actor):
    """Track a home corner, returning eyes and the full respawn cooldown."""

    home: Cell = (0, 0)
    previous: Cell | None = None
    active: bool = True
    respawn_left: float = 0.0
    returning: bool = False
    return_speed: float = 0.0
    personality: int = 0


class Game:
    """Own a complete run, using fixed simulation steps of 1/120 second."""

    STEP = 1.0 / 120.0

    def __init__(self, config: GameConfig) -> None:
        """Prepare a menu-state model; generation waits until Start Game."""
        self.config = config
        self.state = State.MENU
        self.rng = random.Random()
        self.cheats = Cheats()
        self.maze: Maze
        self.player = Actor((0, 0))
        self.ghosts: list[Ghost] = []
        self._home_distances: dict[Cell, dict[Cell, int]] = {}
        self.pellets: set[Cell] = set()
        self.powers: set[Cell] = set()
        self.score = 0
        self.lives = config.lives
        self.level_index = 0
        self.time_left = 0.0
        self.power_left = 0.0
        self.invulnerable_left = 0.0
        self.boost_left = 0.0
        self.transition_left = 0.0
        self.reason = ""
        self.desired: Direction | None = None
        self._accumulator = 0.0

    def start(self) -> None:
        """Reset every run-specific value and build the fixed-seed level."""
        self.score = 0
        self.lives = self.config.lives
        self.level_index = 0
        self.cheats = Cheats()
        self.reason = ""
        self._accumulator = 0.0
        self._load_level()

    def _load_level(self) -> None:
        """Adapt the assigned generator, reserve starts and fill corridors."""
        settings = self.config.levels[self.level_index]
        seed = self.config.seed if self.level_index == 0 else 0
        self.maze = Maze.generate(settings.width, settings.height, seed)
        self.player = Actor(self.maze.spawn)
        self.ghosts = [
            Ghost(cell=cell, home=cell, personality=index)
            for index, cell in enumerate(self.maze.ghost_spawns)
        ]
        self._home_distances = {
            ghost.home: self.maze.distances(ghost.home)
            for ghost in self.ghosts
        }
        self.powers = set(self.maze.power_cells)
        reserved = {self.maze.spawn, *self.maze.ghost_spawns, *self.powers}
        eligible = sorted(self.maze.reachable - reserved)
        target = max(self.config.pacgum,
                     math.ceil(len(eligible) * self.config.pellet_coverage))
        # A local RNG makes collectible layout reproducible too; AI owns a
        # separate RNG that the generator's module-global seed cannot reset.
        placement = random.Random(seed if seed else self.rng.getrandbits(64))
        self.pellets = set(placement.sample(
            eligible, min(len(eligible), target),
        ))
        self.time_left = settings.level_max_time
        self.power_left = 0.0
        self.invulnerable_left = 2.0
        self.boost_left = 0.0
        self.transition_left = 0.0
        self.desired = None
        self.state = State.PLAYING

    def set_direction(self, direction: Direction) -> None:
        """Buffer an intersection turn or reverse along the current edge."""
        if self.state != State.PLAYING:
            return
        self.desired = direction
        actor = self.player
        if actor.target is not None and actor.direction is not None:
            dx, dy = actor.direction.delta
            if direction.delta == (-dx, -dy):
                actor.cell, actor.target = actor.target, actor.cell
                actor.progress = 1.0 - actor.progress
                actor.direction = direction

    def pause(self) -> None:
        """Pause or resume without changing simulation time."""
        if self.state == State.PLAYING:
            self.state = State.PAUSED
        elif self.state == State.PAUSED:
            self.state = State.PLAYING

    def return_to_menu(self) -> None:
        """Discard an unfinished run without recording a score."""
        self.state = State.MENU
        self._accumulator = 0.0

    def update(self, elapsed: float) -> None:
        """Advance finite elapsed time and freeze every timer on pause."""
        if (self.state not in {State.PLAYING, State.TRANSITION}
                or not math.isfinite(elapsed) or elapsed <= 0):
            return
        self._accumulator += elapsed
        while self._accumulator + 1e-12 >= self.STEP:
            self._accumulator -= self.STEP
            if self.state == State.TRANSITION:
                self.transition_left -= self.STEP
                if self.transition_left <= 1e-9:
                    self.level_index += 1
                    self._load_level()
            elif self.state == State.PLAYING:
                self._step(self.STEP)
            else:
                self._accumulator = 0.0
                break

    def _step(self, dt: float) -> None:
        """Update timers, actors, collections and collisions in safe order."""
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left <= 1e-9:
            self.finish_loss("Time ran out")
            return
        self.power_left = max(0.0, self.power_left - dt)
        self.invulnerable_left = max(0.0, self.invulnerable_left - dt)
        self.boost_left = max(0.0, self.boost_left - dt)
        speed = self.config.player_speed * (1.75 if self.boost_left else 1)
        self._move_player(speed * dt)
        if self.state != State.PLAYING:
            return
        for ghost in self.ghosts:
            if not ghost.active:
                self._update_inactive_ghost(ghost, dt)
                continue
            if not self.cheats.frozen:
                difficulty = min(1.35, 1.0 + self.level_index * 0.035)
                frightened = 0.70 if self.power_left > 0 else 1.0
                self._move_ghost(ghost, self.config.ghost_speed * dt
                                 * difficulty * frightened)
        self._collisions()

    def _move_player(self, distance: float) -> None:
        """Spend movement distance only on reciprocal, validated open edges."""
        actor = self.player
        while distance > 1e-10:
            if actor.target is None:
                if self.desired is not None:
                    target = self.maze.step(actor.cell, self.desired)
                    if target is not None:
                        actor.direction = self.desired
                if actor.direction is None:
                    self._collect()
                    break
                actor.target = self.maze.step(actor.cell, actor.direction)
                if actor.target is None:
                    self._collect()
                    break
            used = min(distance, 1.0 - actor.progress)
            actor.progress += used
            distance -= used
            if actor.progress >= 1.0 - 1e-10:
                actor.cell = actor.target
                actor.target = None
                actor.progress = 0.0
                self._collect()
                if self.state != State.PLAYING:
                    break

    def _move_ghost(self, ghost: Ghost, distance: float) -> None:
        """Choose a chase/flee neighbor whenever a ghost reaches a junction."""
        while distance > 1e-10:
            if ghost.target is None:
                frightened = self.power_left > 0
                if frightened:
                    target = self.player.cell
                else:
                    blinky = (self.ghosts[0].cell if self.ghosts
                              else self.player.cell)
                    target = calculate_ghost_target(
                        ghost.personality, ghost.cell, ghost.home,
                        self.player.cell, self.player.direction,
                        blinky, self.maze,
                    )
                ghost.target = choose_step(
                    self.maze, ghost.cell, target, ghost.previous,
                    frightened, self.rng,
                )
                if ghost.target == ghost.cell:
                    ghost.target = None
                    break
                delta = (ghost.target[0] - ghost.cell[0],
                         ghost.target[1] - ghost.cell[1])
                ghost.direction = next(
                    d for d in Direction if d.delta == delta
                )
            used = min(distance, 1.0 - ghost.progress)
            ghost.progress += used
            distance -= used
            if ghost.progress >= 1.0 - 1e-10:
                ghost.previous = ghost.cell
                ghost.cell = ghost.target
                ghost.target = None
                ghost.progress = 0.0

    def _eat_ghost(self, ghost: Ghost) -> None:
        """Send harmless eyes home continuously, awarding this capture once."""
        if not ghost.active:
            return
        distances = self._home_distances[ghost.home]
        remaining = float(distances[ghost.cell])
        if ghost.target is not None:
            forward = 1.0 - ghost.progress + distances[ghost.target]
            backward = ghost.progress + distances[ghost.cell]
            if backward < forward:
                ghost.cell, ghost.target = ghost.target, ghost.cell
                ghost.progress = 1.0 - ghost.progress
            remaining = min(forward, backward)
            delta = (ghost.target[0] - ghost.cell[0],
                     ghost.target[1] - ghost.cell[1])
            ghost.direction = next(d for d in Direction if d.delta == delta)
        ghost.active = False
        ghost.previous = None
        ghost.respawn_left = self.config.ghost_respawn_delay
        ghost.returning = remaining > 1e-10
        # Adapt harmless eye travel to the route so even large mazes retain
        # the configured cooldown, leaving time to wait visibly at home.
        travel_budget = max(0.1, self.config.ghost_respawn_delay - 0.75)
        ghost.return_speed = max(6.0, remaining / travel_budget)
        if not ghost.returning:
            ghost.reset(ghost.home)
            ghost.return_speed = 0.0
        self.score += self.config.points_per_ghost

    def _move_returning_ghost(self, ghost: Ghost, distance: float) -> None:
        """Follow shortest legal passages to this ghost's assigned home."""
        distances = self._home_distances[ghost.home]
        while ghost.returning:
            if ghost.target is None:
                if ghost.cell == ghost.home:
                    ghost.returning = False
                    ghost.return_speed = 0.0
                    break
                ghost.target = min(self.maze.neighbors(ghost.cell),
                                   key=lambda cell: (distances[cell], cell))
                delta = (ghost.target[0] - ghost.cell[0],
                         ghost.target[1] - ghost.cell[1])
                ghost.direction = next(
                    d for d in Direction if d.delta == delta
                )
            if distance <= 1e-10:
                break
            used = min(distance, 1.0 - ghost.progress)
            ghost.progress += used
            distance -= used
            if ghost.progress >= 1.0 - 1e-10:
                ghost.cell = ghost.target
                ghost.target = None
                ghost.progress = 0.0

    def _update_inactive_ghost(self, ghost: Ghost, dt: float) -> None:
        """Restore a body only after both home arrival and cooldown expiry."""
        ghost.respawn_left = max(0.0, ghost.respawn_left - dt)
        if ghost.returning and not self.cheats.frozen:
            self._move_returning_ghost(ghost, ghost.return_speed * dt)
        if not ghost.returning and ghost.respawn_left <= 1e-9:
            ghost.reset(ghost.home)
            ghost.previous = None
            ghost.active = True
            ghost.return_speed = 0.0

    def _collect(self) -> None:
        """Consume each item once; require both normal and power pellets."""
        cell = self.player.cell
        if cell in self.pellets:
            self.pellets.remove(cell)
            self.score += self.config.points_per_pacgum
        if cell in self.powers:
            self.powers.remove(cell)
            self.score += self.config.points_per_super_pacgum
            self.power_left = self.config.power_duration
        if not self.pellets and not self.powers:
            self.complete_level()

    def _collisions(self) -> None:
        """Resolve continuous contacts once, including edge crossings."""
        px, py = self.player.position()
        for ghost in self.ghosts:
            if not ghost.active:
                continue
            gx, gy = ghost.position()
            if (px - gx) ** 2 + (py - gy) ** 2 > 0.56 ** 2:
                continue
            if self.power_left > 0:
                self._eat_ghost(ghost)
            elif (self.invulnerable_left <= 0
                  and not self.cheats.invincible):
                self.lose_life()
                break

    def lose_life(self) -> None:
        """Remove one life and reset actors, preserving score/items/time."""
        if self.state != State.PLAYING:
            return
        self.lives = max(0, self.lives - 1)
        if self.lives == 0:
            self.finish_loss("No lives remaining")
            return
        self.player.reset(self.maze.spawn)
        self.desired = None
        self.power_left = 0.0
        self.invulnerable_left = 2.0
        for ghost in self.ghosts:
            if ghost.active:
                ghost.reset(ghost.home)
                ghost.previous = None

    def complete_level(self) -> None:
        """Announce completion, or win once the final configured level ends."""
        if self.state != State.PLAYING:
            return
        if self.level_index + 1 == len(self.config.levels):
            self.state = State.VICTORY
            self.reason = "Every maze cleared. Congratulations!"
        else:
            self.state = State.TRANSITION
            self.transition_left = 1.5

    def finish_loss(self, reason: str) -> None:
        """Finish a live run with an explicit, player-readable loss reason."""
        if self.state in {State.PLAYING, State.PAUSED}:
            self.reason = reason
            self.state = State.GAME_OVER

    def cheat(self, key: str) -> None:
        """Apply documented review actions only inside an enabled live run."""
        if key == "f1" and self.state == State.PLAYING:
            self.cheats.toggle()
            if not self.cheats.enabled:
                self.boost_left = 0.0
            return
        if not self.cheats.enabled or self.state != State.PLAYING:
            return
        if key == "i":
            self.cheats.invincible = not self.cheats.invincible
        elif key == "g":
            self.cheats.frozen = not self.cheats.frozen
        elif key == "n":
            self.complete_level()
        elif key == "l":
            self.lives = min(999, self.lives + 1)
        elif key == "b":
            self.boost_left = 10.0
        elif key == "o":
            self.power_left = self.config.power_duration
        elif key == "t":
            self.time_left = min(self.time_left, 1.0)
        elif key == "k":
            self.lose_life()
        elif key == "c":
            remaining = self.pellets | self.powers
            keep = min(remaining) if remaining else None
            self.pellets = {keep} if keep is not None else set()
            self.powers.clear()
