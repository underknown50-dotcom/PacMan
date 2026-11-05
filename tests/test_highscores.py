"""Unit tests covering Pac-Man highscore persistence and sanitization."""

import os
import tempfile
import unittest
from pacman.highscores import HighscoreManager


class TestHighscoreManager(unittest.TestCase):
    """Test highscore sorting, persistence, and regex sanitization."""

    def setUp(self) -> None:
        """Create a temporary file for isolated highscore tests."""
        self.temp_file = tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
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


if __name__ == "__main__":
    unittest.main()
