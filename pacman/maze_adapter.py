"""Interpret the assigned MazeGenerator without changing its maze or code."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


Cell = tuple[int, int]


class MazeError(Exception):
    """Report an unavailable generator or an unsafe generated maze."""


class Direction(Enum):
    """Represent movement in screen coordinates, where y grows downward."""

    UP = "up"
    RIGHT = "right"
    DOWN = "down"
    LEFT = "left"

    @property
    def delta(self) -> Cell:
        """Return the change in x and y for one cell of movement."""
        return _DIRECTION_DATA[self][0]


_DIRECTION_DATA: Mapping[Direction, tuple[Cell, int, int]] = {
    Direction.UP: ((0, -1), 1, 4),
    Direction.RIGHT: ((1, 0), 2, 8),
    Direction.DOWN: ((0, 1), 4, 1),
    Direction.LEFT: ((-1, 0), 8, 2),
}


@dataclass(frozen=True)
class Maze:
    """Hold a frozen wall grid and its largest connected playable region.

    Every wall is copied from the installed dependency, never altered. The
    protected four-walled ``42`` cells remain visible in ``walls`` but cannot
    appear in ``reachable``, entity spawns or collectible positions.
    """

    width: int
    height: int
    walls: tuple[tuple[int, ...], ...]
    adjacency: Mapping[Cell, tuple[Cell, ...]]
    reachable: frozenset[Cell]
    spawn: Cell
    ghost_spawns: tuple[Cell, ...]
    power_cells: frozenset[Cell]

    @classmethod
    def generate(cls, width: int, height: int, seed: int) -> Maze:
        """Generate and validate a maze through the original public API.

        Positive seeds are repeatable; zero asks this wheel for randomness.
        No fallback generator is used when the dependency is unavailable.
        """
        if (type(width) is not int or type(height) is not int
                or not 15 <= width <= 35 or not 15 <= height <= 35):
            raise MazeError("Maze dimensions must be integers from 15 to 35.")
        if type(seed) is not int or seed < 0:
            raise MazeError("Maze seed must be a non-negative integer.")
        try:
            from mazegenerator import MazeGenerator
        except ImportError as error:
            raise MazeError(
                "The assigned maze generator is missing. Run make install."
            ) from error
        try:
            generator = MazeGenerator(
                size=(width, height),
                perfect=False,
                entry_cell=(0, 0),
                exit_cell=(width - 1, height - 1),
                seed=seed,
            )
            raw_walls = generator.maze
        except Exception as error:
            raise MazeError(
                "The assigned maze generator could not create this level."
            ) from error
        walls = _freeze_walls(raw_walls, width, height)
        graph = _build_graph(walls, width, height)
        reachable = _largest_component(graph)
        if len(reachable) < 9:
            raise MazeError("The generated maze has too few connected cells.")
        center = (width // 2, height // 2)
        spawn = center if center in reachable else min(
            reachable,
            key=lambda cell: (
                (2 * cell[0] - width + 1) ** 2
                + (2 * cell[1] - height + 1) ** 2,
                cell[1], cell[0],
            ),
        )
        corners = (
            (0, 0), (width - 1, 0),
            (width - 1, height - 1), (0, height - 1),
        )
        reserved = {spawn}
        ghosts: list[Cell] = []
        for corner in corners:
            cell = _nearest_available(corner, reachable, reserved)
            ghosts.append(cell)
            reserved.add(cell)
        powers: set[Cell] = set()
        for corner in corners:
            cell = _nearest_available(corner, reachable, reserved)
            powers.add(cell)
            reserved.add(cell)
        playable_graph = {
            cell: graph[cell] for cell in graph if cell in reachable
        }
        return cls(
            width=width,
            height=height,
            walls=walls,
            adjacency=MappingProxyType(playable_graph),
            reachable=reachable,
            spawn=spawn,
            ghost_spawns=tuple(ghosts),
            power_cells=frozenset(powers),
        )

    def neighbors(self, cell: Cell) -> tuple[Cell, ...]:
        """Return valid adjacent cells, or no cells outside the play region."""
        return self.adjacency.get(cell, ())

    def step(self, cell: Cell, direction: Direction) -> Cell | None:
        """Move one cell only through a reciprocal, in-bounds passage."""
        dx, dy = direction.delta
        destination = (cell[0] + dx, cell[1] + dy)
        return destination if destination in self.neighbors(cell) else None

    def distances(self, origin: Cell) -> dict[Cell, int]:
        """Calculate shortest distances using breadth-first search."""
        if origin not in self.reachable:
            return {}
        distances = {origin: 0}
        pending = deque([origin])
        while pending:
            current = pending.popleft()
            for neighbor in self.neighbors(current):
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    pending.append(neighbor)
        return distances


def _freeze_walls(
    raw_walls: object, width: int, height: int,
) -> tuple[tuple[int, ...], ...]:
    """Copy a correctly shaped grid containing only four-bit integer masks."""
    if not isinstance(raw_walls, (list, tuple)) or len(raw_walls) != height:
        raise MazeError("The generated maze has an invalid height.")
    rows: list[tuple[int, ...]] = []
    for row in raw_walls:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise MazeError("The generated maze has an invalid row width.")
        if any(type(mask) is not int or not 0 <= mask <= 15 for mask in row):
            raise MazeError("The generated maze has an invalid wall mask.")
        rows.append(tuple(row))
    return tuple(rows)


def _build_graph(
    walls: tuple[tuple[int, ...], ...], width: int, height: int,
) -> dict[Cell, tuple[Cell, ...]]:
    """Check borders and reciprocal walls before interpreting open passages."""
    graph: dict[Cell, tuple[Cell, ...]] = {}
    for y, row in enumerate(walls):
        for x, mask in enumerate(row):
            neighbors: list[Cell] = []
            for (dx, dy), bit, opposite in _DIRECTION_DATA.values():
                nx, ny = x + dx, y + dy
                blocked = bool(mask & bit)
                if not (0 <= nx < width and 0 <= ny < height):
                    if not blocked:
                        raise MazeError("The generated maze has an open edge.")
                    continue
                if blocked != bool(walls[ny][nx] & opposite):
                    raise MazeError(
                        "The generated maze has inconsistent passage walls."
                    )
                if not blocked:
                    neighbors.append((nx, ny))
            if neighbors:
                graph[(x, y)] = tuple(neighbors)
    return graph


def _largest_component(
    graph: Mapping[Cell, tuple[Cell, ...]],
) -> frozenset[Cell]:
    """Select the largest connected region, resolving ties in grid order."""
    remaining = set(graph)
    largest: set[Cell] = set()
    for start in graph:
        if start not in remaining:
            continue
        component = {start}
        pending = deque([start])
        remaining.remove(start)
        while pending:
            current = pending.popleft()
            for neighbor in graph[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        if len(component) > len(largest):
            largest = component
    return frozenset(largest)


def _nearest_available(
    corner: Cell, reachable: frozenset[Cell], reserved: set[Cell],
) -> Cell:
    """Find a distinct valid corner-region position by geometric distance.

    Ghosts reserve the exact corners first. Power pellets use the nearest
    remaining positions in the corresponding regions, avoiding spawn overlap.
    """
    candidates = reachable.difference(reserved)
    if not candidates:
        raise MazeError("The generated maze has no safe corner positions.")
    return min(
        candidates,
        key=lambda cell: (
            (cell[0] - corner[0]) ** 2 + (cell[1] - corner[1]) ** 2,
            cell[1], cell[0],
        ),
    )
