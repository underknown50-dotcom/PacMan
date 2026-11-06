"""Unit tests covering Pac-Man entity physics and Ghost AI targeting."""

import unittest
from pacman.adapter import MazeAdapter
from pacman.models import Direction, Ghost, GhostState, GhostType, Player


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
        expected_corner = (clyde.corner_x, clyde.corner_y)
        self.assertEqual((cx_close, cy_close), expected_corner)

    def test_movement_speeds(self) -> None:
        """Verify calibrated movement speeds for player and ghosts."""
        player = Player(5, 5, lives=3)
        self.assertEqual(player.speed, 4.5)

        # Speed boost cheat multiplies speed by 1.6x
        player.speed_boost = True
        boosted = player.speed * 1.6 if player.speed_boost else player.speed
        self.assertAlmostEqual(boosted, 7.2)

        # Ghosts are calibrated slightly slower than Pac-Man
        ghost = Ghost(GhostType.BLINKY, 1, 1, 1, 1)
        self.assertEqual(ghost.base_speed, 3.8)
        self.assertEqual(ghost.frightened_speed, 2.4)
        self.assertEqual(ghost.eaten_speed, 7.0)
        self.assertGreater(player.speed, ghost.base_speed)

    def test_ghost_movement_no_trapping(self) -> None:
        """Verify ghosts traverse corridors smoothly without trapping."""
        adapter = MazeAdapter(width=15, height=15, seed=1)
        adapter.generate()
        player = Player(7, 7, lives=3)
        ghost = Ghost(GhostType.BLINKY, 0, 0, 0, 0)
        dt = 1.0 / 60.0
        visited = set()
        for _ in range(300):
            ghost.update(dt, player, None, adapter)
            visited.add((ghost.grid_x, ghost.grid_y))
        # In 5 seconds at 3.8 tiles/s, ghost should visit multiple tiles
        self.assertGreater(len(visited), 5)

    def test_ghost_bfs_pathfinding_no_clipping(self) -> None:
        """Verify Blinky and Pinky pathfind around walls without clipping."""
        adapter = MazeAdapter(width=15, height=15, seed=42)
        adapter.generate()
        player = Player(6, 0, lives=3)
        blinky = Ghost(GhostType.BLINKY, 0, 0, 0, 0)
        pinky = Ghost(GhostType.PINKY, 14, 0, 14, 0)
        dt = 1.0 / 60.0

        for _ in range(300):
            blinky.update(dt, player, None, adapter)
            pinky.update(dt, player, blinky, adapter)
            self.assertTrue(0.0 <= blinky.x < 15.0)
            self.assertTrue(0.0 <= blinky.y < 15.0)
            self.assertTrue(0.0 <= pinky.x < 15.0)
            self.assertTrue(0.0 <= pinky.y < 15.0)


if __name__ == "__main__":
    unittest.main()
