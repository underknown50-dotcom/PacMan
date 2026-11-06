"""Verify launch boundaries and recoverable diagnostics in the real UI."""

from importlib.util import module_from_spec, spec_from_file_location
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable, cast
from unittest.mock import patch

import pytest

from pacman.app import App
from pacman.configuration import GameConfig
from pacman.error_logging import ErrorLogSession
from pacman.highscores import HighScoreStore
from pacman.maze_adapter import MazeError
from pacman.models import State


ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def headless_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make standalone invocation independent of the host desktop session."""
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")


def test_cli_failure_keeps_details_only_in_log(tmp_path: Path) -> None:
    """Persist the real JSON error traceback without exposing it on stderr."""
    config = tmp_path / "broken.json"
    config.write_text("{broken", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "pac-man.py"), str(config)],
        cwd=ROOT, text=True, capture_output=True, timeout=10,
        env={**os.environ, "XDG_DATA_HOME": str(tmp_path / "data")},
    )
    assert result.returncode == 2
    assert "Configuration error" in result.stderr
    assert "Traceback" not in result.stderr
    log = tmp_path / "data" / "forty-two-pacman" / "errors.log"
    text = log.read_text(encoding="utf-8")
    assert "Traceback" in text and "Invalid JSON" in text
    assert "pacman.launcher" in text


def test_unexpected_runtime_failure_is_logged_and_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contain a failed event loop at the launcher and release the window."""
    import pygame
    specification = spec_from_file_location(
        "pacman_entry", ROOT / "pac-man.py",
    )
    assert specification is not None and specification.loader is not None
    entry = module_from_spec(specification)
    specification.loader.exec_module(entry)
    monkeypatch.setattr(sys, "argv", ["pac-man.py", str(ROOT / "config.json")])
    monkeypatch.delenv("PACMAN_SMOKE_TEST", raising=False)
    monkeypatch.setattr(entry, "ErrorLogSession",
                        lambda **kwargs: ErrorLogSession(tmp_path, **kwargs))
    with patch.object(App, "run",
                      side_effect=RuntimeError("event loop failed")):
        assert cast(Callable[[], int], entry.main)() == 1
    assert not pygame.display.get_init()
    text = (tmp_path / "errors.log").read_text(encoding="utf-8")
    assert "RuntimeError: event loop failed" in text and "Traceback" in text


def test_maze_failure_is_logged_and_menu_remains_usable(
    tmp_path: Path,
) -> None:
    """Retain failure details and allow the player to retry a level."""
    with ErrorLogSession(tmp_path / "logs"):
        app = App(GameConfig(), HighScoreStore(tmp_path / "scores.json"))
        try:
            with patch("pacman.models.Maze.generate",
                       side_effect=MazeError("generator unavailable")):
                app.start()
            assert app.page == "error" and app.game.state == State.MENU
            app.draw()
            app.start()
            assert cast(State, app.game.state) == State.PLAYING
        finally:
            app.graphics.close()
    text = (tmp_path / "logs" / "errors.log").read_text(encoding="utf-8")
    assert "Unable to prepare maze" in text and "Traceback" in text


def test_config_named_like_the_log_is_preserved(tmp_path: Path) -> None:
    """An unrestricted configuration filename cannot become its own log."""
    data = tmp_path / "data"
    directory = data / "forty-two-pacman"
    directory.mkdir(parents=True)
    config = directory / "errors.log"
    original = (ROOT / "config.json").read_bytes()
    config.write_bytes(original)
    result = subprocess.run(
        [sys.executable, str(ROOT / "pac-man.py"), str(config)],
        cwd=ROOT, text=True, capture_output=True, timeout=30,
        env={**os.environ, "XDG_DATA_HOME": str(data),
             "PACMAN_SMOKE_TEST": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert config.read_bytes() == original
    assert (directory / "errors-2.log").is_file()


def test_runtime_log_failure_is_visible_without_score_warning(
    tmp_path: Path,
) -> None:
    """Show a lost log sink on menu/end without corrupting scores."""
    with ErrorLogSession(tmp_path / "logs") as session:
        app = App(GameConfig(), HighScoreStore(tmp_path / "scores.json"),
                  session)
        try:
            handlers = logging.getLogger().handlers
            file_handler = next(handler for handler in handlers
                                if isinstance(handler, RotatingFileHandler)
                                and handler.baseFilename == str(session.path))
            with patch.object(file_handler, "shouldRollover",
                              side_effect=OSError("disk unavailable")):
                logging.getLogger(__name__).warning("A recorded problem")
            assert session.warning and not app.warning
            with patch.object(app.graphics, "text",
                              wraps=app.graphics.text) as draw_text:
                app.draw()
                messages = [str(call.args[0])
                            for call in draw_text.call_args_list]
                assert any("Error log unavailable" in item
                           for item in messages)
                assert not any("Score file warning" in item
                               for item in messages)
                app.start()
                app.game.finish_loss("Time ran out")
                app.draw()
                assert any("Error log unavailable" in str(call.args[0])
                           for call in draw_text.call_args_list)
        finally:
            app.graphics.close()
