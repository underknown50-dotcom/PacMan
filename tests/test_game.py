"""Unit tests covering Pac-Man configuration, highscores, and maze logic.

Satisfies Chapter 3.3 test suite guideline by testing edge cases:
- Faulty/corrupted JSON configuration syntax.
- Out-of-bounds parameters and comment stripping.
- Highscore name sanitization and ranking.
- Maze corridor accessibility and boundary checks.
- Ghost targeting personalities (Blinky, Pinky, Clyde).
- Game state progression and cheat mode toggles.
"""

import os
import tempfile
import unittest
from pacman.adapter import MazeAdapter
from pacman.config import ConfigLoader, GameConfig
from pacman.game import Game
from pacman.highscores import HighscoreManager
from pacman.models import Direction, Ghost, GhostState, GhostType, Player


class TestConfigLoader(unittest.TestCase):
    """Test defensive JSON loading, comment stripping, and edge cases."""

    def test_strip_comments(self) -> None:
        """Verify '#' comments, trailing commas, and block comments."""
        raw = (
            "# Top level comment\n"
            "/* Multi-line\n"
            "   C-style block comment */\n"
            "{\n"
            '    "lives": 5, # In-line comment\n'
            '    // C-style comment\n'
            '    "name": "level#1", // string with hash\n'
            '    "seed": 99, // trailing comma below\n'
            "}\n"
        )
        cleaned = ConfigLoader.strip_comments(raw)
        self.assertNotIn("# Top level", cleaned)
        self.assertNotIn("C-style block", cleaned)
        self.assertNotIn("// C-style", cleaned)
        self.assertIn('"lives": 5', cleaned)
        self.assertIn('"level#1"', cleaned)

    def test_case_insensitive_keys(self) -> None:
        """Verify uppercase and titlecase keys are recognized properly."""
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as f:
            f.write(
                '{"LIVES": 6, "Seed": 99, "Points_Per_Pacgum": 35, '
                '"LEVELS": [{"Level": 1, "Width": 17, "Height": 17}]}'
            )
            path = f.name

        try:
            cfg = ConfigLoader.load(path)
            self.assertEqual(cfg.lives, 6)
            self.assertEqual(cfg.seed, 99)
            self.assertEqual(cfg.points_per_pacgum, 35)
            self.assertEqual(cfg.levels[0].width, 17)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_key_aliases(self) -> None:
        """Verify indicative aliases like 'pacgum' and 'time' are read."""
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as f:
            f.write(
                '{"pacgum": 42, "super_pacgum": 100, "ghost": 500, "time": 65}'
            )
            path = f.name

        try:
            cfg = ConfigLoader.load(path)
            self.assertEqual(cfg.points_per_pacgum, 42)
            self.assertEqual(cfg.points_per_super_pacgum, 100)
            self.assertEqual(cfg.points_per_ghost, 500)
            self.assertEqual(cfg.level_max_time, 65)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_missing_file_fallback(self) -> None:
        """Verify missing file does not raise an exception."""
        cfg = ConfigLoader.load("non_existent_file_xyz_123.json")
        self.assertEqual(cfg.lives, 3)
        self.assertEqual(len(cfg.levels), 10)

    def test_clamping_values(self) -> None:
        """Verify out-of-range values clamp to safe limits."""
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as f:
            f.write(
                '{"lives": -10, "points_per_pacgum": -50, '
                '"level_max_time": 9999}'
            )
            path = f.name

        try:
            cfg = ConfigLoader.load(path)
            self.assertEqual(cfg.lives, ConfigLoader.MIN_LIVES)
            self.assertEqual(cfg.points_per_pacgum, ConfigLoader.MIN_POINTS)
            self.assertEqual(cfg.level_max_time, ConfigLoader.MAX_TIME)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_corrupt_json_syntax_fallback(self) -> None:
        """Verify malformed JSON falls back gracefully without traceback."""
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as f:
            f.write("{ this is completely broken json syntax !!! ")
            path = f.name

        try:
            cfg = ConfigLoader.load(path)
            self.assertEqual(cfg.lives, 3)
            self.assertEqual(cfg.seed, 42)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_unknown_keys_ignored(self) -> None:
        """Verify unrecognized keys are ignored without error."""
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as f:
            f.write(
                '{"unknown_test_key_xyz": 12345, "lives": 4, "seed": 77}'
            )
            path = f.name

        try:
            cfg = ConfigLoader.load(path)
            self.assertEqual(cfg.lives, 4)
            self.assertEqual(cfg.seed, 77)
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestHighscoreManager(unittest.TestCase):
    """Test highscore persistence, sanitization, and sorting."""

    def setUp(self) -> None:
        """Create a temporary file for highscores."""
        self.temp_file = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        )
        self.temp_file.close()
        self.manager = HighscoreManager(self.temp_file.name)

    def tearDown(self) -> None:
        """Clean up temporary highscore file."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_name_sanitization(self) -> None:
        """Verify name is clamped to 10 chars, alphanumeric and spaces."""
        self.assertEqual(
            HighscoreManager.sanitize_name("Alice!!@@##$$"), "Alice"
        )
        self.assertEqual(
            HighscoreManager.sanitize_name("SuperLongPlayerName123"),
            "SuperLongP",
        )
        self.assertEqual(HighscoreManager.sanitize_name(""), "Player")

    def test_top_10_sorting(self) -> None:
        """Verify scores are sorted in descending order and capped at 10."""
        for i in range(15):
            self.manager.add_score(f"User{i}", i * 100)

        entries = self.manager.get_top_entries()
        self.assertEqual(len(entries), 10)
        self.assertEqual(entries[0][1], 1400)
        self.assertEqual(entries[-1][1], 500)

    def test_corrupt_highscore_recovery(self) -> None:
        """Verify corrupt file does not crash and starts with clean list."""
        with open(self.temp_file.name, "w", encoding="utf-8") as f:
            f.write("corrupted non-json contents")

        new_manager = HighscoreManager(self.temp_file.name)
        self.assertEqual(len(new_manager.scores), 0)


class TestMazeAdapter(unittest.TestCase):
    """Test maze adapter wrapping and fallback mechanics."""

    def test_generation_dimensions(self) -> None:
        """Verify generated maze matches requested dimensions."""
        adapter = MazeAdapter(width=15, height=15, seed=42)
        grid = adapter.generate()
        self.assertEqual(len(grid), 15)
        self.assertEqual(len(grid[0]), 15)

    def test_safe_center_and_corners(self) -> None:
        """Verify safe center is walkable and 4 corners are returned."""
        adapter = MazeAdapter(width=15, height=15, seed=42)
        adapter.generate()
        cx, cy = adapter.find_safe_center()
        self.assertFalse(adapter.is_solid(cx, cy))

        corners = adapter.find_four_corners()
        self.assertEqual(len(corners), 4)
        for cor_x, cor_y in corners:
            self.assertFalse(adapter.is_solid(cor_x, cor_y))

    def test_can_move_walls(self) -> None:
        """Verify movement cannot pass through walls."""
        adapter = MazeAdapter(width=15, height=15, seed=42)
        adapter.generate()
        # Outer boundary check (0, 0) moving West or North should be blocked
        self.assertFalse(adapter.can_move(0, 0, -1, 0))
        self.assertFalse(adapter.can_move(0, 0, 0, -1))


class TestEntitiesAndAI(unittest.TestCase):
    """Test Player and Ghost entity behaviors and AI targeting."""

    def test_player_invincibility_cheat(self) -> None:
        """Verify player invincibility toggle."""
        player = Player(5, 5, lives=3)
        self.assertFalse(player.is_invincible)
        player.is_invincible = True
        self.assertTrue(player.is_invincible)

    def test_ghost_frightened_state(self) -> None:
        """Verify ghost transitions to frightened mode and back."""
        ghost = Ghost(GhostType.BLINKY, 1, 1, 1, 1)
        self.assertEqual(ghost.state, GhostState.CHASE)
        ghost.trigger_frightened(8.0)
        self.assertEqual(ghost.state, GhostState.FRIGHTENED)
        self.assertEqual(ghost.direction, Direction.DOWN)

    def test_ghost_targeting_blinky_pinky_clyde(self) -> None:
        """Verify distinct targeting math for Blinky, Pinky, and Clyde."""
        player = Player(10, 10, lives=3)
        player.direction = Direction.RIGHT

        # Blinky targets player tile directly
        blinky = Ghost(GhostType.BLINKY, 1, 1, 1, 1)
        bx, by = blinky._calculate_target(player, None)
        self.assertEqual((bx, by), (10, 10))

        # Pinky targets 4 tiles ahead of player direction
        pinky = Ghost(GhostType.PINKY, 1, 1, 1, 1)
        px, py = pinky._calculate_target(player, blinky)
        self.assertEqual((px, py), (14, 10))

        # Clyde targets player if distance > 8, retreats if <= 8
        clyde = Ghost(GhostType.CLYDE, 1, 1, 1, 1)
        cx, cy = clyde._calculate_target(player, blinky)
        self.assertEqual((cx, cy), (10, 10))

        # Move Clyde close (e.g. at 9, 10 -> distance 1 <= 8)
        clyde.grid_x, clyde.grid_y = 9, 10
        cx_close, cy_close = clyde._calculate_target(player, blinky)
        cx_c, cy_c = cx_close, cy_close
        self.assertEqual((cx_c, cy_c), (clyde.corner_x, clyde.corner_y))

    def test_game_cheat_skip_level(self) -> None:
        """Verify cheat level skip advances level correctly."""
        cfg = GameConfig()
        game = Game(cfg)
        game.start_new_game()
        self.assertEqual(game.current_level_idx, 0)
        game.cheat_skip_level()
        self.assertEqual(game.current_level_idx, 1)


if __name__ == "__main__":
    unittest.main()
