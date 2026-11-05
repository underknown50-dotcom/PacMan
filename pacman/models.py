"""Entity models and AI state machines for Pac-Man.

Includes:
- Direction vector representations and helpers.
- Player (Pac-Man) entity with buffered input and corridor movement.
- Ghost entity hierarchy with classic arcade targeting behaviors:
  * Blinky (Red): Direct chaser.
  * Pinky (Pink): Ambush predictor (4 tiles ahead).
  * Inky (Cyan): Flanker (vector reflection with Blinky).
  * Clyde (Orange): Distance-based coward (retreats when within 8 tiles).
- Frightened and Eaten ghost states, timers, and pathfinding.
"""

import math
import random
from enum import Enum, auto
from typing import List, Optional, Tuple
from pacman.adapter import MazeAdapter


class Direction(Enum):
    """Corridor movement directions with (dx, dy) coordinate deltas."""

    NONE = (0, 0)
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

    @property
    def dx(self) -> int:
        """Horizontal step delta."""
        return self.value[0]

    @property
    def dy(self) -> int:
        """Vertical step delta."""
        return self.value[1]

    def opposite(self) -> "Direction":
        """Return the opposite direction."""
        if self == Direction.UP:
            return Direction.DOWN
        if self == Direction.DOWN:
            return Direction.UP
        if self == Direction.LEFT:
            return Direction.RIGHT
        if self == Direction.RIGHT:
            return Direction.LEFT
        return Direction.NONE


class GhostState(Enum):
    """Operational states for ghost AI."""

    CHASE = auto()
    SCATTER = auto()
    FRIGHTENED = auto()
    EATEN = auto()


class GhostType(Enum):
    """The four classic ghost personalities."""

    BLINKY = "Blinky"  # Red
    PINKY = "Pinky"    # Pink
    INKY = "Inky"      # Cyan
    CLYDE = "Clyde"    # Orange


class Player:
    """Represents Pac-Man, tracking lives, position, and buffered input."""

    def __init__(self, start_x: int, start_y: int, lives: int = 3) -> None:
        """Initialize Pac-Man at the specified grid coordinate."""
        self.spawn_x = start_x
        self.spawn_y = start_y
        self.x = float(start_x)
        self.y = float(start_y)
        self.grid_x = start_x
        self.grid_y = start_y
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE
        self.lives = lives
        self.speed = 4.5  # Tiles per second
        self.is_invincible = False
        self.speed_boost = False

    def reset_position(self) -> None:
        """Reset Pac-Man back to the center spawn position."""
        self.grid_x = self.spawn_x
        self.grid_y = self.spawn_y
        self.x = float(self.spawn_x)
        self.y = float(self.spawn_y)
        self.direction = Direction.NONE
        self.next_direction = Direction.NONE

    def queue_direction(self, direction: Direction) -> None:
        """Buffer a desired turn direction."""
        self.next_direction = direction

    def update(self, dt: float, maze: MazeAdapter) -> None:
        """Update position along corridors, respecting walls."""
        effective_speed = (
            self.speed * 1.6 if self.speed_boost else self.speed
        )
        move_dist = effective_speed * dt

        # Check if 180-degree immediate reversal is requested
        if (
            self.next_direction != Direction.NONE
            and self.next_direction == self.direction.opposite()
        ):
            self.direction = self.next_direction
            self.next_direction = Direction.NONE

        # Attempt to make queued turn if aligned near grid center
        dist_to_center = math.hypot(
            self.x - self.grid_x, self.y - self.grid_y
        )
        if dist_to_center < 0.15 and self.next_direction != Direction.NONE:
            if maze.can_move(
                self.grid_x,
                self.grid_y,
                self.next_direction.dx,
                self.next_direction.dy,
            ):
                self.x = float(self.grid_x)
                self.y = float(self.grid_y)
                self.direction = self.next_direction
                self.next_direction = Direction.NONE

        # Advance along current direction
        if self.direction != Direction.NONE:
            # Check if moving towards a wall
            can_advance = maze.can_move(
                self.grid_x, self.grid_y, self.direction.dx, self.direction.dy
            )

            target_x = self.x + self.direction.dx * move_dist
            target_y = self.y + self.direction.dy * move_dist

            if can_advance:
                self.x = target_x
                self.y = target_y
                # Discrete grid coordinate when crossing midpoint
                self.grid_x = int(round(self.x))
                self.grid_y = int(round(self.y))
            else:
                # Clamp to cell center when hitting wall
                if self.direction in (Direction.LEFT, Direction.RIGHT):
                    if (
                        self.direction == Direction.RIGHT
                        and target_x > self.grid_x
                    ) or (
                        self.direction == Direction.LEFT
                        and target_x < self.grid_x
                    ):
                        self.x = float(self.grid_x)
                        self.direction = Direction.NONE
                    else:
                        self.x = target_x
                elif self.direction in (Direction.UP, Direction.DOWN):
                    if (
                        self.direction == Direction.DOWN
                        and target_y > self.grid_y
                    ) or (
                        self.direction == Direction.UP
                        and target_y < self.grid_y
                    ):
                        self.y = float(self.grid_y)
                        self.direction = Direction.NONE
                    else:
                        self.y = target_y


class Ghost:
    """Ghost entity featuring authentic arcade AI pathfinding."""

    COLORS = {
        GhostType.BLINKY: (255, 0, 0),       # Red
        GhostType.PINKY: (255, 184, 255),    # Pink
        GhostType.INKY: (0, 255, 255),       # Cyan
        GhostType.CLYDE: (255, 184, 82),     # Orange
    }

    def __init__(
        self,
        ghost_type: GhostType,
        spawn_x: int,
        spawn_y: int,
        corner_x: int,
        corner_y: int,
    ) -> None:
        """Initialize the ghost with personality and assigned corner."""
        self.ghost_type = ghost_type
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.corner_x = corner_x
        self.corner_y = corner_y

        self.x = float(spawn_x)
        self.y = float(spawn_y)
        self.grid_x = spawn_x
        self.grid_y = spawn_y

        self.direction = Direction.UP
        self.state = GhostState.CHASE
        self.base_speed = 3.8
        self.eaten_speed = 7.0
        self.frightened_speed = 2.4

        self.frightened_timer = 0.0
        self.frightened_duration = 8.0
        self.respawn_timer = 0.0
        self.is_frozen = False

    def reset_position(self) -> None:
        """Reset ghost to its corner spawn position."""
        self.grid_x = self.spawn_x
        self.grid_y = self.spawn_y
        self.x = float(self.spawn_x)
        self.y = float(self.spawn_y)
        self.direction = Direction.UP
        self.state = GhostState.CHASE
        self.frightened_timer = 0.0
        self.respawn_timer = 0.0

    def trigger_frightened(self, duration: float = 8.0) -> None:
        """Enter frightened (edible) mode when Pac-Man eats super-pacgum."""
        if self.state != GhostState.EATEN:
            self.state = GhostState.FRIGHTENED
            self.frightened_duration = duration
            self.frightened_timer = duration
            # Classic behavior: reverse direction on frightened trigger
            self.direction = self.direction.opposite()

    def mark_eaten(self) -> None:
        """Transition to eaten state when touched by Pac-Man in edible mode."""
        self.state = GhostState.EATEN
        self.frightened_timer = 0.0
        self.respawn_timer = 6.0

    def update(
        self,
        dt: float,
        player: Player,
        blinky: Optional["Ghost"],
        maze: MazeAdapter,
    ) -> None:
        """Update ghost movement, targeting, and state timers."""
        if self.is_frozen:
            return

        # Handle timers
        if self.state == GhostState.FRIGHTENED:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                self.state = GhostState.CHASE
        elif self.state == GhostState.EATEN:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.reset_position()
                return

        # Determine current movement speed
        if self.state == GhostState.EATEN:
            speed = self.eaten_speed
        elif self.state == GhostState.FRIGHTENED:
            speed = self.frightened_speed
        else:
            speed = self.base_speed

        move_dist = speed * dt

        # When close to cell midpoint, calculate next turn direction
        dist_to_center = math.hypot(
            self.x - self.grid_x, self.y - self.grid_y
        )
        if dist_to_center < move_dist:
            self.x = float(self.grid_x)
            self.y = float(self.grid_y)
            self._choose_next_direction(player, blinky, maze)

        # Advance along direction
        if self.direction != Direction.NONE:
            if maze.can_move(
                self.grid_x, self.grid_y, self.direction.dx, self.direction.dy
            ):
                self.x += self.direction.dx * move_dist
                self.y += self.direction.dy * move_dist
                self.grid_x = int(round(self.x))
                self.grid_y = int(round(self.y))
            else:
                self.x = float(self.grid_x)
                self.y = float(self.grid_y)
                self._choose_next_direction(player, blinky, maze)

    def _choose_next_direction(
        self,
        player: Player,
        blinky: Optional["Ghost"],
        maze: MazeAdapter,
    ) -> None:
        """Select the next corridor direction at intersections."""
        valid_dirs: List[Direction] = []
        all_dirs = [
            Direction.UP,
            Direction.LEFT,
            Direction.DOWN,
            Direction.RIGHT,
        ]

        for d in all_dirs:
            # Ghosts cannot immediately reverse unless forced
            if d == self.direction.opposite() and len(all_dirs) > 1:
                continue
            if maze.can_move(self.grid_x, self.grid_y, d.dx, d.dy):
                valid_dirs.append(d)

        if not valid_dirs:
            # Dead-end reversal
            rev = self.direction.opposite()
            if maze.can_move(self.grid_x, self.grid_y, rev.dx, rev.dy):
                self.direction = rev
            return

        if self.state == GhostState.FRIGHTENED:
            # Frightened mode: pick randomly among valid paths
            self.direction = random.choice(valid_dirs)
            return

        # Target calculation based on ghost personality
        target_x, target_y = self._calculate_target(player, blinky)

        # Choose valid direction that minimizes Euclidean distance to target
        best_dir = valid_dirs[0]
        best_dist = float("inf")

        for d in valid_dirs:
            next_x = self.grid_x + d.dx
            next_y = self.grid_y + d.dy
            dist = (next_x - target_x) ** 2 + (next_y - target_y) ** 2
            if dist < best_dist:
                best_dist = dist
                best_dir = d

        self.direction = best_dir

    def _calculate_target(
        self, player: Player, blinky: Optional["Ghost"]
    ) -> Tuple[int, int]:
        """Calculate target grid tile based on AI personality."""
        if self.state == GhostState.EATEN:
            # Return straight to assigned corner
            return self.spawn_x, self.spawn_y

        px, py = player.grid_x, player.grid_y
        pdx, pdy = player.direction.dx, player.direction.dy

        # 1. Blinky (Red): Direct aggressive chaser
        if self.ghost_type == GhostType.BLINKY:
            return px, py

        # 2. Pinky (Pink): Ambush 4 tiles ahead of Pac-Man
        if self.ghost_type == GhostType.PINKY:
            return px + (4 * pdx), py + (4 * pdy)

        # 3. Inky (Cyan): Flanking pinch maneuver with Blinky
        if self.ghost_type == GhostType.INKY:
            pivot_x = px + (2 * pdx)
            pivot_y = py + (2 * pdy)
            bx = blinky.grid_x if blinky else px
            by = blinky.grid_y if blinky else py
            # Vector reflection from Blinky through pivot tile
            target_x = pivot_x + (pivot_x - bx)
            target_y = pivot_y + (pivot_y - by)
            return target_x, target_y

        # 4. Clyde (Orange): Cowardly distance-based behavior
        if self.ghost_type == GhostType.CLYDE:
            dist = math.hypot(self.grid_x - px, self.grid_y - py)
            if dist > 8.0:
                return px, py
            # Retreat to bottom-left corner when too close
            return self.corner_x, self.corner_y

        return px, py
