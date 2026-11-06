"""Launch the game with exactly one JSON configuration path."""

from pathlib import Path
import logging
import os
import sys

from pacman.error_logging import ErrorLogSession


LOGGER = logging.getLogger("pacman.launcher")


def main() -> int:
    """Own logging and report failures without console tracebacks."""
    protected = (Path(sys.argv[1]),) if len(sys.argv) == 2 else ()
    with ErrorLogSession(protected_paths=protected) as session:
        try:
            return _launch(session)
        except KeyboardInterrupt:
            return 0
        except Exception as exc:
            destination = (str(session.path)
                           if session.path and not session.warning
                           else "the console (file log unavailable)")
            LOGGER.exception(
                "The game could not continue: %s. Error details: %s",
                exc, destination,
            )
            return 1


def _launch(session: ErrorLogSession) -> int:
    """Validate one config argument, load services and release the frontend."""
    if len(sys.argv) != 2:
        LOGGER.error("Usage: python3 pac-man.py <configuration-file>")
        return 2
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        from pacman.configuration import (
            ConfigurationError, load_config, resolve_highscore_path,
        )
        config_path = Path(sys.argv[1])
        config = load_config(config_path)
        score_path = resolve_highscore_path(config.highscore_filename,
                                            config_path)
    except (ConfigurationError, OSError, RuntimeError, RecursionError) as exc:
        LOGGER.exception("Configuration error: %s", exc)
        return 2
    try:
        from pacman.app import App
        from pacman.graphics import GraphicsError
        from pacman.highscores import HighScoreStore
    except ImportError as exc:
        LOGGER.exception("Missing runtime dependency: %s. Run 'make install'.",
                         exc)
        return 1
    scores = HighScoreStore(score_path)
    scores.load()
    app: App | None = None
    try:
        app = App(config, scores, session)
        if os.environ.get("PACMAN_SMOKE_TEST") == "1":
            from pacman.smoke import exercise
            exercise(app)
        else:
            app.run()
    except GraphicsError as exc:
        LOGGER.exception("Graphics error: %s", exc)
        return 1
    finally:
        if app is not None:
            app.graphics.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
