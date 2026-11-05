"""Unit tests covering Game engine state machine, progression, and cheats."""

import unittest
from pacman.config import GameConfig
from pacman.game import Game, GameState


class TestGameEngine(unittest.TestCase):
    """Test game state machine, level transitions, and reviewer cheat suite."""

    def setUp(self) -> None:
        """Create game instance with default configuration."""
        self.cfg = GameConfig()
        self.game = Game(self.cfg)

    def test_initial_state(self) -> None:
        """Verify game starts in MENU state with default score and lives."""
        self.assertEqual(self.game.state, GameState.MENU)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.player.lives, 3)

    def test_start_new_game(self) -> None:
        """Verify starting game transitions to PLAYING and spawns dots."""
        self.game.start_new_game()
        self.assertEqual(self.game.state, GameState.PLAYING)
        self.assertEqual(self.game.current_level_idx, 0)
        self.assertGreater(len(self.game.pacgums), 0)
        self.assertEqual(len(self.game.super_pacgums), 4)

    def test_pause_toggle(self) -> None:
        """Verify pausing and unpausing toggles state correctly."""
        self.game.start_new_game()
        self.game.toggle_pause()
        self.assertEqual(self.game.state, GameState.PAUSED)
        self.game.toggle_pause()
        self.assertEqual(self.game.state, GameState.PLAYING)

    def test_cheat_skip_level(self) -> None:
        """Verify cheat level skip advances level correctly."""
        self.game.start_new_game()
        self.assertEqual(self.game.current_level_idx, 0)
        self.game.cheat_skip_level()
        self.assertEqual(self.game.current_level_idx, 1)

    def test_cheat_invincibility_toggle(self) -> None:
        """Verify cheat invincibility toggles player invincibility."""
        self.game.start_new_game()
        self.assertFalse(self.game.player.is_invincible)
        self.game.cheat_toggle_invincibility()
        self.assertTrue(self.game.player.is_invincible)
        self.assertIn("INVINCIBLE", self.game.active_cheats)


if __name__ == "__main__":
    unittest.main()
