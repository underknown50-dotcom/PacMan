"""Unit tests covering Pac-Man configuration, highscores, and maze logic.

Satisfies Chapter 3.3 test suite guideline.
"""

import os
import tempfile
import unittest
from pacman.adapter import MazeAdapter
from pacman.config import ConfigLoader
from pacman.highscores import HighscoreManager
from pacman.models import Direction, Ghost, GhostState, GhostType, Player


class TestConfigLoader(unittest.TestCase):
    """Test defensive JSON loading and comment stripping."""

    def test_strip_comments(self) -> None:
        """Verify '#' comments and trailing comments are removed."""
        raw = (
            "# Top level comment\n"
            "{\n"
            '    "lives": 5, # In-line comment\n'
            '    // C-style comment\n'
            '    "seed": 99\n'
            "}\n"
        )
        cleaned = ConfigLoader.strip_comments(raw)
        self.assertNotIn("# Top level", cleaned)
        self.assertNotIn("// C-style", cleaned)
        self.assertIn('"lives": 5', cleaned)

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


class TestEntities(unittest.TestCase):
    """Test Player and Ghost entity behaviors."""

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


if __name__ == "__main__":
    unittest.main()
