"""Choose wall-respecting ghost moves independently from drawing and clocks."""

from __future__ import annotations

import random

from pacman.maze_adapter import Cell, Direction, Maze


def nearest_reachable(maze: Maze, target: tuple[int, int]) -> Cell:
    """Find the closest reachable maze cell to any (x, y) coordinate."""
    if target in maze.reachable:
        return target
    tx, ty = target
    return min(
        maze.reachable,
        key=lambda c: ((c[0] - tx) ** 2 + (c[1] - ty) ** 2, c[1], c[0]),
    )


def calculate_ghost_target(
    personality: int,
    cell: Cell,
    home: Cell,
    player_cell: Cell,
    player_direction: Direction | None,
    blinky_cell: Cell,
    maze: Maze,
) -> Cell:
    """Compute targeting cell according to arcade ghost personalities.

    0 (Blinky / Red): Directly targets Pac-Man's current cell.
    1 (Pinky / Pink): Targets 4 tiles ahead in Pac-Man's facing direction.
    2 (Inky / Cyan): Flanks by reflecting Blinky across pivot 2 tiles ahead.
    3 (Clyde / Orange): Chases when > 8 tiles away; retreats home when <= 8.
    """
    mode = personality % 4
    if mode == 0:
        return player_cell
    if mode == 1:
        if player_direction is not None:
            p_dx, p_dy = player_direction.delta
            raw = (player_cell[0] + 4 * p_dx, player_cell[1] + 4 * p_dy)
            return nearest_reachable(maze, raw)
        return player_cell
    if mode == 2:
        if player_direction is not None:
            p_dx, p_dy = player_direction.delta
            pivot = (player_cell[0] + 2 * p_dx, player_cell[1] + 2 * p_dy)
        else:
            pivot = player_cell
        raw = (2 * pivot[0] - blinky_cell[0], 2 * pivot[1] - blinky_cell[1])
        return nearest_reachable(maze, raw)
    # mode == 3 (Clyde)
    dist_sq = (cell[0] - player_cell[0]) ** 2 + (cell[1] - player_cell[1]) ** 2
    if dist_sq > 64:
        return player_cell
    return home


def choose_step(
    maze: Maze,
    cell: Cell,
    player: Cell,
    previous: Cell | None,
    frightened: bool,
    rng: random.Random,
) -> Cell:
    """Chase along shortest routes, or flee along the most distant route.

    An independent random source varies equally good choices. A reversal is
    avoided among ties, but remains possible when it is the best available
    move. A ghost waits only when its cell has no legal passage.
    """
    neighbors = maze.neighbors(cell)
    if not neighbors:
        return cell
    distances = maze.distances(player)
    unreachable = len(maze.reachable) + 1
    values = {
        neighbor: distances.get(neighbor, unreachable)
        for neighbor in neighbors
    }
    best = max(values.values()) if frightened else min(values.values())
    choices = [neighbor for neighbor in neighbors if values[neighbor] == best]
    forward = [neighbor for neighbor in choices if neighbor != previous]
    return rng.choice(forward or choices)
