"""Keep persistent rotating diagnostics and brief, readable console output."""

from __future__ import annotations

import copy
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import time
from types import TracebackType
from typing import TYPE_CHECKING, Callable, TextIO

from pacman.configuration import _user_data_directory


if TYPE_CHECKING:
    _ConsoleBase = logging.StreamHandler[TextIO]
else:
    _ConsoleBase = logging.StreamHandler


class _BriefFormatter(logging.Formatter):
    """Keep exception details out of console output using a record copy."""

    def __init__(self, original: logging.Formatter | None) -> None:
        """Retain an existing console format without traceback output."""
        super().__init__()
        self._original = original or logging.Formatter(
            "%(levelname)s: %(message)s",
        )

    def format(self, record: logging.LogRecord) -> str:
        """Remove traceback fields only from the copy sent to a console."""
        brief = copy.copy(record)
        brief.exc_info = None
        brief.exc_text = None
        brief.stack_info = None
        return self._original.format(brief).replace("\r", " ").replace(
            "\n", " ",
        )


class _UTCFormatter(logging.Formatter):
    """Render persistent timestamps in UTC independently of host timezone."""

    converter = staticmethod(time.gmtime)


class _ConsoleHandler(_ConsoleBase):
    """Avoid logging-internal tracebacks when a console stream disappears."""

    def handleError(self, record: logging.LogRecord) -> None:
        """Tolerate an unavailable console without recursive diagnostics."""


class _FileHandler(RotatingFileHandler):
    """Disable failed persistence without logging's internal stderr dump."""

    def __init__(
        self, path: Path, max_bytes: int, backup_count: int,
        report_failure: Callable[[str], None],
    ) -> None:
        """Open one rotating UTF-8 log with a controlled failure callback."""
        self.failed = False
        self._report_failure = report_failure
        super().__init__(
            path, maxBytes=max_bytes, backupCount=backup_count,
            encoding="utf-8", errors="backslashreplace",
        )

    def emit(self, record: logging.LogRecord) -> None:
        """Write a record only while this destination remains usable."""
        if not self.failed:
            super().emit(record)

    def handleError(self, record: logging.LogRecord) -> None:
        """Report the first file error and suppress logging-internal dumps."""
        if self.failed:
            return
        self.failed = True
        error = sys.exc_info()[1]
        self._report_failure(str(error) if error else "log write failed")


def _is_console_handler(handler: logging.Handler) -> bool:
    """Identify actual stdout/stderr handlers without changing caplog files."""
    if not isinstance(handler, logging.StreamHandler):
        return False
    if isinstance(handler, logging.FileHandler):
        return False
    stream: object = handler.stream
    return any(stream is item for item in (
        sys.stderr, sys.stdout, sys.__stderr__, sys.__stdout__,
    ))


class ErrorLogSession:
    """Own rotating error diagnostics while preserving caller logging state.

    The default directory matches persistent scores in XDG user data. A valid
    configured JSON or packaged installation never needs to be writable.
    Existing console handlers are reused; their formatters and the previous
    root level are restored on close. Other handlers, including caplog, retain
    ownership and keep receiving original records and exception information.
    """

    def __init__(
        self, directory: Path | None = None, max_bytes: int = 1_048_576,
        backup_count: int = 3, protected_paths: tuple[Path, ...] = (),
    ) -> None:
        """Configure a bounded user-data log without opening resources yet."""
        if (isinstance(max_bytes, bool) or not isinstance(max_bytes, int)
                or max_bytes <= 0):
            raise ValueError("max_bytes must be a positive integer")
        if (isinstance(backup_count, bool) or not isinstance(backup_count, int)
                or backup_count < 1):
            raise ValueError("backup_count must be at least one")
        self.path: Path | None = None
        self._directory = directory
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._protected_paths = protected_paths
        self._warning = ""
        self._root = logging.getLogger()
        self._previous_level = self._root.level
        self._active = False
        self._file_handler: _FileHandler | None = None
        self._console_handler: logging.Handler | None = None
        self._formatters: list[
            tuple[logging.Handler, logging.Formatter | None, _BriefFormatter]
        ] = []

    @property
    def warning(self) -> str:
        """Return the latest persistence warning for the game interface."""
        return self._warning

    def _choose_path(self, directory: Path) -> Path:
        """Keep the log and every rotation name clear of active input files."""
        protected = {path.resolve() for path in self._protected_paths}
        index = 1
        while True:
            filename = "errors.log" if index == 1 else f"errors-{index}.log"
            path = directory / filename
            destinations = [path] + [
                directory / f"{filename}.{number}"
                for number in range(1, self._backup_count + 1)
            ]
            if all(item.resolve() not in protected for item in destinations):
                return path
            index += 1

    def __enter__(self) -> ErrorLogSession:
        """Attach owned resources and retain usable console-only fallback."""
        if self._active:
            return self
        self._active = True
        self._warning = ""
        self.path = None
        self._previous_level = self._root.level
        self._root.setLevel(min(self._previous_level, logging.INFO))
        consoles = [handler for handler in self._root.handlers
                    if _is_console_handler(handler)]
        for handler in consoles:
            original = handler.formatter
            brief = _BriefFormatter(original)
            self._formatters.append((handler, original, brief))
            handler.setFormatter(brief)
        if not consoles:
            console = _ConsoleHandler(sys.stderr)
            console.setLevel(logging.WARNING)
            console.setFormatter(_BriefFormatter(None))
            self._root.addHandler(console)
            self._console_handler = console
        try:
            directory = self._directory or _user_data_directory()
            directory.mkdir(parents=True, exist_ok=True)
            path = self._choose_path(directory)
            file_handler = _FileHandler(
                path, self._max_bytes, self._backup_count, self._file_failed,
            )
            file_handler.setFormatter(_UTCFormatter(
                "%(asctime)sZ %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            ))
            self._root.addHandler(file_handler)
            self._file_handler = file_handler
            self.path = path
        except (OSError, RuntimeError, ValueError) as error:
            self._file_failed(str(error))
        return self

    def _file_failed(self, detail: str) -> None:
        """Disable the file and report one short visible warning."""
        handler = self._file_handler
        self._file_handler = None
        if handler is not None:
            self._root.removeHandler(handler)
            try:
                handler.close()
            except (OSError, ValueError):
                pass
        if not self._warning:
            concise = " ".join(detail.split())
            self._warning = (
                "File logging unavailable; console logging continues: "
                + concise
            )
            self._root.warning("%s", self._warning)

    def close(self) -> None:
        """Close owned handlers, restore caller state and tolerate repeats."""
        if not self._active:
            return
        handler = self._file_handler
        self._file_handler = None
        if handler is not None:
            self._root.removeHandler(handler)
            try:
                handler.close()
            except (OSError, ValueError) as error:
                self._file_failed(str(error))
        for existing, original, brief in self._formatters:
            if existing.formatter is brief:
                existing.setFormatter(original)
        self._formatters.clear()
        if self._console_handler is not None:
            self._root.removeHandler(self._console_handler)
            self._console_handler.close()
            self._console_handler = None
        self._root.setLevel(self._previous_level)
        self._active = False

    def __exit__(
        self, exception_type: type[BaseException] | None,
        exception: BaseException | None, traceback: TracebackType | None,
    ) -> None:
        """Always release session resources without hiding caller errors."""
        self.close()
