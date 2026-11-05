"""Game controller and state machine for Pac-Man.

Coordinates the main game loop, level generation, player and ghost updates,
collision detection, scoring, cheat modes, and menu state transitions.
"""

import math
import random
from enum import Enum, auto
from typing import List, Optional, Set, Tuple
from pacman.adapter import MazeAdapter
from pacman.config import GameConfig, LevelConfig
from pacman.highscores import HighscoreManager
from pacman.models import Direction, Ghost, GhostState, GhostType, Player


class GameState(Enum):
    """Overall game state progression."""

    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    HIGHSCORES = auto()
    INSTRUCTIONS = auto()


class Game:
    """Central game orchestrator managing rules, entities, and progression."""

    def __init__(self, config: GameConfig) -> None:
        """Initialize the game with verified configuration."""
        self.config = config
        self.highscores = HighscoreManager(config.highscore_filename)

        self.state = GameState.MENU
        self.score = 0
        self.current_level_idx = 0
        self.level_time_remaining = float(config.level_max_time)

        self.maze: MazeAdapter = MazeAdapter()
        self.player: Player = Player(0, 0, lives=config.lives)
        self.ghosts: List[Ghost] = []
        self.blinky: Optional[Ghost] = None

        self.pacgums: Set[Tuple[int, int]] = set()
        self.super_pacgums: Set[Tuple[int, int]] = set()

        self.ghosts_eaten_combo = 0
        self.name_input = ""
        self.active_cheats: Set[str] = set()

        # Build initial level
        self._load_level(self.current_level_idx)

    def _load_level(self, level_index: int) -> None:
        """Construct the maze and entities for the specified level index."""
        self.current_level_idx = level_index
        total_configured = len(self.config.levels)

        if level_index < total_configured:
            lvl_cfg: LevelConfig = self.config.levels[level_index]
        else:
            dim = min(29, 15 + (level_index * 2))
            lvl_cfg = LevelConfig(
                level=level_index + 1,
                width=dim,
                height=dim,
                max_time=self.config.level_max_time,
            )

        # Chapter 6.1: Level 1 has fixed seed, subsequent levels random
        if level_index == 0:
            seed = self.config.seed
        else:
            seed = random.randint(1, 999999)

        self.maze = MazeAdapter(
            width=lvl_cfg.width, height=lvl_cfg.height, seed=seed
        )
        self.maze.generate()
        self.level_time_remaining = float(lvl_cfg.max_time)

        # Locate center spawn and 4 corners
        spawn_x, spawn_y = self.maze.find_safe_center()
        corners = self.maze.find_four_corners()

        # Initialize or relocate player
        if level_index == 0:
            self.player = Player(spawn_x, spawn_y, lives=self.config.lives)
        else:
            self.player.spawn_x = spawn_x
            self.player.spawn_y = spawn_y
            self.player.reset_position()

        # Re-apply any active cheats to player
        if "INVINCIBLE" in self.active_cheats:
            self.player.is_invincible = True
        if "SPEED" in self.active_cheats:
            self.player.speed_boost = True

        # Initialize 4 ghosts in the 4 corners (Chapter 6.1)
        ghost_types = [
            GhostType.BLINKY,  # Top-Left
            GhostType.PINKY,   # Top-Right
            GhostType.INKY,    # Bottom-Left
            GhostType.CLYDE,   # Bottom-Right
        ]
        self.ghosts = []
        for i, g_type in enumerate(ghost_types):
            cx, cy = corners[i % len(corners)]
            ghost = Ghost(
                ghost_type=g_type,
                spawn_x=cx,
                spawn_y=cy,
                corner_x=cx,
                corner_y=cy,
            )
            if "FREEZE" in self.active_cheats:
                ghost.is_frozen = True
            self.ghosts.append(ghost)

        self.blinky = self.ghosts[0]

        # Populate pacgums and super-pacgums (Chapter 6.1)
        # Super-pacgums in the 4 corners
        self.super_pacgums = set(corners)

        # Pacgums in most corridors (excluding corners and player spawn)
        all_cells = self.maze.get_corridor_cells()
        self.pacgums = set()
        for cell in all_cells:
            if cell not in self.super_pacgums and cell != (spawn_x, spawn_y):
                self.pacgums.add(cell)

        self.ghosts_eaten_combo = 0

    def start_new_game(self) -> None:
        """Reset score, lives, and start the campaign at Level 1."""
        self.score = 0
        self.name_input = ""
        self.active_cheats.clear()
        self._load_level(0)
        self.state = GameState.PLAYING

    def handle_direction_input(self, direction: Direction) -> None:
        """Queue player movement direction."""
        if self.state == GameState.PLAYING:
            self.player.queue_direction(direction)

    def toggle_pause(self) -> None:
        """Toggle between playing and paused states."""
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.PLAYING

    # ------------------ Cheat System (Chapter 6.5) ------------------

    def cheat_toggle_invincibility(self) -> None:
        """Toggle invincibility cheat."""
        if "INVINCIBLE" in self.active_cheats:
            self.active_cheats.remove("INVINCIBLE")
            self.player.is_invincible = False
        else:
            self.active_cheats.add("INVINCIBLE")
            self.player.is_invincible = True

    def cheat_skip_level(self) -> None:
        """Instantly complete the current level."""
        if self.state == GameState.PLAYING:
            self._advance_level()

    def cheat_toggle_ghost_freeze(self) -> None:
        """Freeze or unfreeze all ghosts."""
        if "FREEZE" in self.active_cheats:
            self.active_cheats.remove("FREEZE")
            for ghost in self.ghosts:
                ghost.is_frozen = False
        else:
            self.active_cheats.add("FREEZE")
            for ghost in self.ghosts:
                ghost.is_frozen = True

    def cheat_add_life(self) -> None:
        """Grant an additional life."""
        self.player.lives += 1

    def cheat_toggle_speed(self) -> None:
        """Toggle player speed boost."""
        if "SPEED" in self.active_cheats:
            self.active_cheats.remove("SPEED")
            self.player.speed_boost = False
        else:
            self.active_cheats.add("SPEED")
            self.player.speed_boost = True

    # ------------------ Game Update Loop ------------------

    def update(self, dt: float) -> None:
        """Execute one update step."""
        if self.state != GameState.PLAYING:
            return

        # Update countdown timer
        self.level_time_remaining -= dt
        if self.level_time_remaining <= 0:
            self._handle_time_up()
            return

        # Update Player
        self.player.update(dt, self.maze)

        # Check Pacgum consumption
        player_tile = (self.player.grid_x, self.player.grid_y)
        if player_tile in self.pacgums:
            self.pacgums.remove(player_tile)
            self.score += self.config.points_per_pacgum

            # Level victory when all pacgums are cleared
            if not self.pacgums:
                self._advance_level()
                return

        # Check Super-Pacgum consumption
        if player_tile in self.super_pacgums:
            self.super_pacgums.remove(player_tile)
            self.score += self.config.points_per_super_pacgum
            self.ghosts_eaten_combo = 0
            for ghost in self.ghosts:
                ghost.trigger_frightened(8.0)

        # Update Ghosts
        for ghost in self.ghosts:
            ghost.update(dt, self.player, self.blinky, self.maze)

        # Check Ghost collisions
        self._check_ghost_collisions()

    def _check_ghost_collisions(self) -> None:
        """Check for physical overlaps between player and ghosts."""
        for ghost in self.ghosts:
            dist = math.hypot(
                self.player.x - ghost.x, self.player.y - ghost.y
            )
            if dist < 0.75:
                # Ghost in edible state
                if ghost.state == GhostState.FRIGHTENED:
                    ghost.mark_eaten()
                    combo_bonus = (2 ** self.ghosts_eaten_combo)
                    pts = self.config.points_per_ghost * combo_bonus
                    self.score += pts
                    self.ghosts_eaten_combo += 1
                elif ghost.state == GhostState.CHASE:
                    if not self.player.is_invincible:
                        self._handle_player_death()
                        return

    def _handle_player_death(self) -> None:
        """Handle life loss and either respawn or trigger Game Over."""
        self.player.lives -= 1
        if self.player.lives <= 0:
            self.state = GameState.GAME_OVER
            self.name_input = ""
        else:
            self.player.reset_position()
            for ghost in self.ghosts:
                ghost.reset_position()

    def _handle_time_up(self) -> None:
        """Handle timeout condition."""
        if not self.player.is_invincible:
            self._handle_player_death()
        self.level_time_remaining = float(
            self.config.levels[min(
                self.current_level_idx, len(self.config.levels) - 1
            )].max_time
        )

    def _advance_level(self) -> None:
        """Proceed to the next level or complete the game."""
        next_idx = self.current_level_idx + 1
        # Subject specifies at least 10 levels
        if next_idx >= max(10, len(self.config.levels)):
            self.state = GameState.VICTORY
            self.name_input = ""
        else:
            self._load_level(next_idx)

    def submit_highscore(self) -> None:
        """Submit the player's name and transition back to Main Menu."""
        name = self.name_input.strip() or "Player"
        self.highscores.add_score(name, self.score)
        self.name_input = ""
        self.state = GameState.MENU
