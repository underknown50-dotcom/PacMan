"""Adapter module to interface with the external MazeGenerator package.

This module encapsulates the assigned external maze generator library,
ensuring that our game adheres to Chapter 5.4 specifications:
- Uses the assigned package as-is without modification.
- Enforces PERFECT=False for Pac-Man corridor loops.
- Provides clean error handling and safe fallback without tracebacks.
- Calculates safe player spawn, 4 corner positions, and corridor dots.
"""

from collections import deque
from typing import Deque, List, Set, Tuple
from mazegenerator import MazeGenerator


class MazeAdapter:
    """Adapts the external MazeGenerator to our game's grid requirements."""

    WALL_NORTH = 1
    WALL_EAST = 2
    WALL_SOUTH = 4
    WALL_WEST = 8
    SOLID_BLOCK = 15

    def __init__(
        self, width: int = 15, height: int = 15, seed: int = 42
    ) -> None:
        """Initialize the maze adapter with dimensions and generation seed."""
        self.width = max(7, width)
        self.height = max(7, height)
        self.seed = seed
        self.grid: List[List[int]] = []

    def generate(self) -> List[List[int]]:
        """Safely generate the maze grid using the external generator."""
        try:
            # Chapter 5.4 rule: PERFECT must be False to create corridor loops
            generator = MazeGenerator(
                size=(self.width, self.height),
                perfect=False,
                seed=self.seed,
            )
            self.grid = generator.maze
            return self.grid
        except Exception as error:
            print(f"[MazeAdapter Warning] External generator error: {error}")
            print("[MazeAdapter] Falling back to safe default maze.")
            return self._create_fallback_maze()

    def _create_fallback_maze(self) -> List[List[int]]:
        """Generate a safe bordered maze if the external package fails."""
        fallback: List[List[int]] = []
        for y in range(self.height):
            row: List[int] = []
            for x in range(self.width):
                val = 0
                if y == 0:
                    val |= self.WALL_NORTH
                if x == self.width - 1:
                    val |= self.WALL_EAST
                if y == self.height - 1:
                    val |= self.WALL_SOUTH
                if x == 0:
                    val |= self.WALL_WEST
                row.append(val)
            fallback.append(row)
        self.grid = fallback
        return self.grid

    def get_dimensions(self) -> Tuple[int, int]:
        """Return the dimensions as (width, height)."""
        return self.width, self.height

    def is_solid(self, x: int, y: int) -> bool:
        """Check if a cell is an impenetrable solid block (value 15)."""
        if not (0 <= y < len(self.grid) and 0 <= x < len(self.grid[0])):
            return True
        return self.grid[y][x] == self.SOLID_BLOCK

    def can_move(self, x: int, y: int, dx: int, dy: int) -> bool:
        """Check if movement from (x, y) along (dx, dy) is possible.

        A movement is blocked if:
        1. Starting or destination coordinates are out of bounds.
        2. Starting or destination cell is a solid block (15).
        3. Starting cell has a wall in that direction.
        4. Destination cell has the opposing wall.
        """
        if not (0 <= y < self.height and 0 <= x < self.width):
            return False
        if self.grid[y][x] == self.SOLID_BLOCK:
            return False

        nx, ny = x + dx, y + dy
        if not (0 <= ny < self.height and 0 <= nx < self.width):
            return False
        if self.grid[ny][nx] == self.SOLID_BLOCK:
            return False

        curr_cell = self.grid[y][x]
        next_cell = self.grid[ny][nx]

        # Moving North (Up)
        if dx == 0 and dy == -1:
            if (curr_cell & self.WALL_NORTH) or (next_cell & self.WALL_SOUTH):
                return False
        # Moving East (Right)
        elif dx == 1 and dy == 0:
            if (curr_cell & self.WALL_EAST) or (next_cell & self.WALL_WEST):
                return False
        # Moving South (Down)
        elif dx == 0 and dy == 1:
            if (curr_cell & self.WALL_SOUTH) or (next_cell & self.WALL_NORTH):
                return False
        # Moving West (Left)
        elif dx == -1 and dy == 0:
            if (curr_cell & self.WALL_WEST) or (next_cell & self.WALL_EAST):
                return False
        else:
            return False

        return True

    def find_safe_center(self) -> Tuple[int, int]:
        """Find the nearest walkable corridor cell to the center.

        Avoids the central '42' logo blocks which have solid value 15.
        """
        cx = self.width // 2
        cy = self.height // 2
        if not self.is_solid(cx, cy):
            return cx, cy

        visited: Set[Tuple[int, int]] = {(cx, cy)}
        queue: Deque[Tuple[int, int]] = deque([(cx, cy)])
        dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]

        while queue:
            qx, qy = queue.popleft()
            for dx, dy in dirs:
                nx, ny = qx + dx, qy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        if not self.is_solid(nx, ny):
                            return nx, ny
                        queue.append((nx, ny))

        return 1, 1

    def find_nearest_walkable(
        self, target_x: int, target_y: int
    ) -> Tuple[int, int]:
        """Find the nearest walkable corridor cell to a target position."""
        target_x = max(0, min(self.width - 1, target_x))
        target_y = max(0, min(self.height - 1, target_y))
        if not self.is_solid(target_x, target_y):
            return target_x, target_y

        visited: Set[Tuple[int, int]] = {(target_x, target_y)}
        queue: Deque[Tuple[int, int]] = deque([(target_x, target_y)])
        dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]

        while queue:
            qx, qy = queue.popleft()
            for dx, dy in dirs:
                nx, ny = qx + dx, qy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        if not self.is_solid(nx, ny):
                            return nx, ny
                        queue.append((nx, ny))
        return target_x, target_y

    def find_four_corners(self) -> List[Tuple[int, int]]:
        """Return the 4 corner corridor coordinates.

        Corners ordered as:
        1. Top-Left
        2. Top-Right
        3. Bottom-Left
        4. Bottom-Right
        """
        targets = [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        ]
        corners: List[Tuple[int, int]] = []
        for tx, ty in targets:
            corner_cell = self.find_nearest_walkable(tx, ty)
            corners.append(corner_cell)
        return corners

    def get_corridor_cells(self) -> List[Tuple[int, int]]:
        """Return all non-solid cells in the maze."""
        cells: List[Tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if not self.is_solid(x, y):
                    cells.append((x, y))
        return cells
