"""Main executable entry point for 42 Pac-Man.

Adheres strictly to Chapter 5.1 usage:
    $> python3 pac-man.py config.json

Ensures robust defense against corrupt configurations, missing arguments,
or abnormal exits without ever outputting a Python traceback.
"""

import sys
import pygame
from pacman.config import ConfigLoader
from pacman.game import Game, GameState
from pacman.models import Direction
from pacman.renderer import Renderer


def validate_args() -> str:
    """Validate command line arguments according to Chapter 5.1.

    Requires exactly one argument ending in '.json'.
    Exits cleanly with an informative message on error without a traceback.
    """
    if len(sys.argv) != 2:
        print("Usage error: Program requires exactly one argument.")
        print("Format: python3 pac-man.py <config_file.json>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not filepath.lower().endswith(".json"):
        print(
            f"Configuration error: File '{filepath}' does not have a "
            "'.json' extension."
        )
        sys.exit(1)

    return filepath


def run_game_loop(game: Game, renderer: Renderer) -> None:
    """Run the 60 FPS interactive game loop."""
    clock = pygame.time.Clock()
    running = True

    while running:
        # Fixed 60 FPS delta time
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type != pygame.KEYDOWN:
                continue

            # State-specific keyboard dispatch
            if game.state == GameState.MENU:
                if event.key in (pygame.K_UP, pygame.K_w):
                    renderer.menu_cursor = (
                        renderer.menu_cursor - 1
                    ) % len(renderer.menu_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    renderer.menu_cursor = (
                        renderer.menu_cursor + 1
                    ) % len(renderer.menu_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    choice = renderer.menu_cursor
                    if choice == 0:  # Start Game
                        game.start_new_game()
                    elif choice == 1:  # View Highscores
                        game.state = GameState.HIGHSCORES
                    elif choice == 2:  # Instructions
                        game.state = GameState.INSTRUCTIONS
                    elif choice == 3:  # Exit
                        running = False
                elif event.key == pygame.K_ESCAPE:
                    running = False

            elif game.state in (GameState.HIGHSCORES, GameState.INSTRUCTIONS):
                if event.key in (
                    pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE
                ):
                    game.state = GameState.MENU

            elif game.state == GameState.PLAYING:
                # Steering controls
                if event.key in (pygame.K_UP, pygame.K_w):
                    game.handle_direction_input(Direction.UP)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    game.handle_direction_input(Direction.DOWN)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    game.handle_direction_input(Direction.LEFT)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    game.handle_direction_input(Direction.RIGHT)
                elif event.key == pygame.K_p:
                    game.toggle_pause()
                elif event.key == pygame.K_ESCAPE:
                    game.toggle_pause()

                # Chapter 6.5 Cheat Mode Hotkeys
                elif event.key == pygame.K_i:
                    game.cheat_toggle_invincibility()
                elif event.key == pygame.K_l:
                    game.cheat_skip_level()
                elif event.key == pygame.K_f:
                    game.cheat_toggle_ghost_freeze()
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    game.cheat_add_life()
                elif event.key == pygame.K_s:
                    game.cheat_toggle_speed()

            elif game.state == GameState.PAUSED:
                if event.key in (pygame.K_UP, pygame.K_w):
                    renderer.pause_cursor = (
                        renderer.pause_cursor - 1
                    ) % len(renderer.pause_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    renderer.pause_cursor = (
                        renderer.pause_cursor + 1
                    ) % len(renderer.pause_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if renderer.pause_cursor == 0:
                        game.state = GameState.PLAYING
                    else:
                        game.state = GameState.MENU
                elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                    game.state = GameState.PLAYING

            elif game.state in (GameState.GAME_OVER, GameState.VICTORY):
                if event.key == pygame.K_BACKSPACE:
                    game.name_input = game.name_input[:-1]
                elif event.key == pygame.K_RETURN:
                    game.submit_highscore()
                elif event.key == pygame.K_ESCAPE:
                    game.submit_highscore()
                else:
                    char = event.unicode
                    # Name criteria: alphanumeric and spaces, max 10 characters
                    if (
                        len(game.name_input) < 10
                        and (char.isalnum() or char == " ")
                    ):
                        game.name_input += char

        # Update entity positions and timers
        game.update(dt)

        # Draw frame
        renderer.render(dt)

    # Clean shutdown
    game.highscores.save()


def main() -> None:
    """Safely bootstrap and launch the Pac-Man application."""
    config_path = validate_args()

    try:
        config = ConfigLoader.load(config_path)
    except Exception as err:
        print(f"Error loading configuration: {err}. Using defaults.")
        config = ConfigLoader.load("")

    try:
        pygame.init()
        game = Game(config)
        renderer = Renderer(game)
        run_game_loop(game, renderer)
    except KeyboardInterrupt:
        print("\nGame exited by user.")
    except Exception as err:
        print(f"Game error: {err}")
    finally:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
