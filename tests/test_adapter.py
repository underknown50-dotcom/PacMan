"""Unit tests covering external maze generator adapter and bitmasks."""

import unittest
from pacman.adapter import MazeAdapter


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


if __name__ == "__main__":
    unittest.main()
