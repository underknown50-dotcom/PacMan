"""Unit tests covering Pac-Man configuration loading and validation."""

import os
import tempfile
import unittest
from pacman.config import ConfigLoader


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
                '{"pacgum": 42, "super_pacgum": 100, '
                '"ghost": 500, "time": 65}'
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
            f.write('{"unsupported_key_abc": 999, "lives": 4}')
            path = f.name

        try:
            cfg = ConfigLoader.load(path)
            self.assertEqual(cfg.lives, 4)
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
