"""Exercise native SDL events, CLI failures and the complete rendered flow."""

from pathlib import Path
import os
import subprocess
import sys
from typing import cast

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pacman.app import App, DIRECTION_KEYS  # noqa: E402
from pacman.configuration import GameConfig  # noqa: E402
from pacman.graphics import InputEvent  # noqa: E402
from pacman.highscores import HighScoreStore  # noqa: E402
from pacman.maze_adapter import Direction  # noqa: E402
from pacman.models import State  # noqa: E402
from pacman.smoke import exercise  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("arguments", [[], ["config.json", "extra"],
                                       ["missing-config.json"]])
def test_cli_errors(arguments: list[str]) -> None:
    """Report missing/extra arguments and missing config without tracebacks."""
    result = subprocess.run(
        [sys.executable, str(ROOT / 'pac-man.py'), *arguments],
        cwd=ROOT, text=True, capture_output=True, timeout=10,
    )
    assert result.returncode == 2
    assert 'Traceback' not in result.stderr
    assert 'Usage' in result.stderr or 'Configuration error' in result.stderr


def test_bad_json_cli(tmp_path: Path) -> None:
    """Broken whole files fail cleanly regardless of their filename suffix."""
    config = tmp_path / 'not-json.txt'
    config.write_text('{broken', encoding='utf-8')
    result = subprocess.run(
        [sys.executable, str(ROOT / 'pac-man.py'), str(config)],
        text=True, capture_output=True, timeout=10,
    )
    assert result.returncode == 2
    assert 'Invalid JSON' in result.stderr and 'Traceback' not in result.stderr


def test_key_mapping() -> None:
    """Both promised keyboard layouts map to the same four directions."""
    for arrow, letter, direction in (
        ('up', 'w', Direction.UP), ('down', 's', Direction.DOWN),
        ('left', 'a', Direction.LEFT), ('right', 'd', Direction.RIGHT),
    ):
        assert DIRECTION_KEYS[arrow] == DIRECTION_KEYS[letter] == direction


def test_full_headless_flow(tmp_path: Path) -> None:
    """Clear a real level then exercise all ten, saving, restart and exit."""
    store = HighScoreStore(tmp_path / 'scores.json')
    store.load()
    exercise(App(GameConfig(), store))
    restored = HighScoreStore(store.path)
    restored.load()
    assert len(restored.entries) == 2


def test_pause_discard_and_name_feedback(tmp_path: Path) -> None:
    """Confirm discard, reject invalid names and avoid duplicate saves."""
    app = App(GameConfig(), HighScoreStore(tmp_path / 'scores.json'))
    try:
        app.start()
        app.handle(InputEvent('key', key='p'))
        app.handle(InputEvent('key', key='down'))
        app.handle(InputEvent('key', key='enter'))
        assert app.confirm_leave and app.game.state == State.PAUSED
        app.handle(InputEvent('key', key='escape'))
        assert not app.confirm_leave and app.page == 'game'
        app.handle(InputEvent('key', key='enter'))
        app.handle(InputEvent('key', key='enter'))
        assert app.page == 'main' and not app.scores.entries
        app.start()
        app.game.finish_loss('Test loss')
        app.handle(InputEvent('text', text='é!'))
        assert app.name == '' and app.message
        app.handle(InputEvent('key', key='enter'))
        assert app.page == 'game' and app.message
        app.handle(InputEvent('text', text='ABCDEFGHIJK'))
        assert app.name == 'ABCDEFGHIJ' and app.message
        app.handle(InputEvent('key', key='enter'))
        assert app.page == 'main' and len(app.scores.entries) == 1
    finally:
        app.graphics.close()


def test_native_event_adapter(tmp_path: Path) -> None:
    """SDL keyboard, text and close events traverse the real event facade."""
    import pygame
    app = App(GameConfig(), HighScoreStore(tmp_path / 'scores.json'))
    try:
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RETURN, unicode='\r'))
        for event in app.graphics.events():
            app.handle(event)
        assert app.game.state == State.PLAYING
        app.game.finish_loss('Native input test')
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, text='SDL42'))
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RETURN, unicode='\r'))
        for event in app.graphics.events():
            app.handle(event)
        assert app.page == 'main' and app.scores.entries[0].name == 'SDL42'
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        for event in app.graphics.events():
            app.handle(event)
        assert not app.running
    finally:
        app.graphics.close()


def test_generator_failure_returns_safe_screen(tmp_path: Path) -> None:
    """An adapter failure remains readable and the menu can still be used."""
    from unittest.mock import patch
    from pacman.maze_adapter import MazeError
    app = App(GameConfig(), HighScoreStore(tmp_path / 'scores.json'))
    try:
        with patch('pacman.models.Maze.generate',
                   side_effect=MazeError('Assigned generator unavailable')):
            app.start()
        assert app.page == 'error' and app.game.state == State.MENU
        app.draw()
        app.handle(InputEvent('key', key='enter'))
        assert app.page == 'main'
        app.start()
        assert cast(State, app.game.state) == State.PLAYING
    finally:
        app.graphics.close()


def test_deep_corrupt_files_recover(tmp_path: Path) -> None:
    """Excessive nesting is reported like other malformed JSON data."""
    from pacman.configuration import ConfigurationError, load_config
    nested = '[' * 2000 + '0' + ']' * 2000
    config = tmp_path / 'deep.json'
    config.write_text(nested, encoding='utf-8')
    with pytest.raises(ConfigurationError):
        load_config(config)
    store = HighScoreStore(config)
    store.load()
    assert store.last_warning and not store.entries
