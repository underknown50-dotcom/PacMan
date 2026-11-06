"""Verify bounded diagnostics, readable consoles and recoverable log errors."""

from io import StringIO
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
import sys
from typing import TextIO
from unittest.mock import patch

import pytest

from pacman.error_logging import ErrorLogSession


LOGGER = logging.getLogger("pacman.review.logging")


def _file_handler() -> RotatingFileHandler:
    """Find the session's persistent handler without assuming root ordering."""
    return next(
        handler for handler in logging.getLogger().handlers
        if isinstance(handler, RotatingFileHandler)
    )


def test_timestamp_level_module_and_persistence(tmp_path: Path) -> None:
    """A real file persists explicit UTC timestamps, severity and module."""
    with ErrorLogSession(tmp_path) as session:
        assert session.path == tmp_path / "errors.log"
        LOGGER.warning("first run")
    with ErrorLogSession(tmp_path):
        LOGGER.warning("second run")
    contents = (tmp_path / "errors.log").read_text(encoding="utf-8")
    assert re.search(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z WARNING "
        r"pacman.review.logging: first run", contents,
    )
    assert contents.count("first run") == contents.count("second run") == 1


def test_utc_is_not_local_host_time(tmp_path: Path) -> None:
    """A known epoch is formatted in UTC without consulting localtime."""
    with ErrorLogSession(tmp_path):
        record = logging.LogRecord(
            LOGGER.name, logging.ERROR, __file__, 0, "known epoch", (), None,
        )
        record.created = 0
        with patch("time.localtime", side_effect=AssertionError("localtime")):
            LOGGER.handle(record)
    assert (tmp_path / "errors.log").read_text().startswith(
        "1970-01-01T00:00:00Z ERROR pacman.review.logging: known epoch",
    )


def test_rotating_log_has_bounded_size_and_backups(tmp_path: Path) -> None:
    """Repeated records rotate into at most the configured backup count."""
    with ErrorLogSession(tmp_path, max_bytes=240, backup_count=3):
        for number in range(40):
            LOGGER.warning("message %02d %s", number, "x" * 40)
    files = sorted(tmp_path.glob("errors.log*"))
    assert len(files) == 4
    assert {path.name for path in files} == {
        "errors.log", "errors.log.1", "errors.log.2", "errors.log.3",
    }
    assert all(path.stat().st_size <= 240 for path in files)
    assert "message 39" in (tmp_path / "errors.log").read_text()


def test_traceback_stays_in_file_and_original_record(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Console formatting cannot remove the traceback from file/caplog."""
    with ErrorLogSession(tmp_path):
        try:
            raise ValueError("private diagnostic detail")
        except ValueError:
            LOGGER.exception("Game could not continue")
    console = capsys.readouterr().err
    assert "ERROR: Game could not continue" in console
    assert "Traceback" not in console
    assert "private diagnostic detail" not in console
    contents = (tmp_path / "errors.log").read_text()
    assert "Traceback (most recent call last)" in contents
    assert "ValueError: private diagnostic detail" in contents
    original = next(
        record for record in caplog.records
        if record.message == "Game could not continue"
    )
    assert original.exc_info is not None


def test_existing_console_reused_and_formatter_restored(
    tmp_path: Path,
) -> None:
    """Existing console handlers retain ownership and their old format."""
    root = logging.getLogger()
    console = StringIO()
    original_formatter = logging.Formatter("EXISTING %(message)s")
    with patch.object(sys, "stderr", console):
        handler: logging.StreamHandler[TextIO] = logging.StreamHandler(
            sys.stderr,
        )
        handler.setFormatter(original_formatter)
        root.addHandler(handler)
        handlers_before = list(root.handlers)
        level_before = root.level
        try:
            with ErrorLogSession(tmp_path):
                assert root.handlers[:-1] == handlers_before
                try:
                    raise RuntimeError("file detail")
                except RuntimeError:
                    LOGGER.exception("one console line")
            assert root.handlers == handlers_before
            assert root.level == level_before
            assert handler.formatter is original_formatter
            assert console.getvalue() == "EXISTING one console line\n"
            assert not console.closed
        finally:
            root.removeHandler(handler)
            handler.close()


def test_existing_memory_handler_and_caplog_preserved(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    """Nonconsole handlers keep their own formatting and original records."""
    root = logging.getLogger()
    memory = StringIO()
    handler: logging.StreamHandler[StringIO] = logging.StreamHandler(memory)
    formatter = logging.Formatter("MEMORY %(message)s")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    handlers_before = list(root.handlers)
    level_before = root.level
    try:
        with ErrorLogSession(tmp_path):
            LOGGER.warning("captured")
            assert handler.formatter is formatter
        assert root.handlers == handlers_before
        assert root.level == level_before
        assert memory.getvalue() == "MEMORY captured\n"
        assert any(record.message == "captured" for record in caplog.records)
    finally:
        root.removeHandler(handler)
        handler.close()


def test_repeated_sessions_do_not_fan_out(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Sequential sessions leave no stale root handlers or duplicate lines."""
    root = logging.getLogger()
    handlers_before = list(root.handlers)
    for number in range(4):
        with ErrorLogSession(tmp_path):
            LOGGER.warning("session %d", number)
        assert root.handlers == handlers_before
    console = capsys.readouterr().err
    contents = (tmp_path / "errors.log").read_text()
    for number in range(4):
        assert console.count(f"session {number}") == 1
        assert contents.count(f"session {number}") == 1


def test_file_open_failure_is_visible_and_nonfatal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """An unwritable destination still provides brief console diagnostics."""
    with patch(
        "logging.FileHandler._open", side_effect=PermissionError("read only"),
    ):
        with ErrorLogSession(tmp_path) as session:
            assert session.path is None
            assert "read only" in session.warning
            LOGGER.error("still visible")
    console = capsys.readouterr().err
    assert "File logging unavailable" in console
    assert "still visible" in console
    assert "Traceback" not in console
    assert "--- Logging error ---" not in console


def test_directory_failure_is_nonfatal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """A file occupying the data directory cannot prevent game startup."""
    destination = tmp_path / "occupied"
    destination.write_text("existing file")
    with ErrorLogSession(destination) as session:
        assert session.path is None
        assert session.warning
        LOGGER.error("continue without file")
    assert "continue without file" in capsys.readouterr().err
    assert destination.read_text() == "existing file"


def test_disk_full_disables_file_without_internal_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed write is reported once and future logs stay on the console."""
    with ErrorLogSession(tmp_path) as session:
        handler = _file_handler()
        stream = handler.stream
        assert stream is not None
        with patch.object(stream, "write", side_effect=OSError("disk full")):
            LOGGER.error("failed persistent message")
        assert handler not in logging.getLogger().handlers
        assert stream is not None
        assert stream.closed
        assert "disk full" in session.warning
        LOGGER.error("later console message")
    console = capsys.readouterr().err
    assert console.count("File logging unavailable") == 1
    assert "failed persistent message" in console
    assert "later console message" in console
    assert "Traceback" not in console
    assert "--- Logging error ---" not in console


def test_rollover_failure_preserves_existing_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """A rename failure disables file logging and preserves the old data."""
    path = tmp_path / "errors.log"
    path.write_text("earlier diagnostic\n")
    with ErrorLogSession(tmp_path, max_bytes=30) as session:
        with patch(
            "logging.handlers.os.rename",
            side_effect=PermissionError("rotation denied"),
        ):
            LOGGER.error("new diagnostic exceeds this small log")
        assert "rotation denied" in session.warning
        assert not any(
            isinstance(handler, RotatingFileHandler)
            for handler in logging.getLogger().handlers
        )
        LOGGER.error("console survives rotation")
    assert path.read_text() == "earlier diagnostic\n"
    console = capsys.readouterr().err
    assert "console survives rotation" in console
    assert "--- Logging error ---" not in console


def test_context_exception_closes_owned_file_and_restores_level(
    tmp_path: Path,
) -> None:
    """Caller exceptions propagate while every owned resource is released."""
    root = logging.getLogger()
    handlers_before = list(root.handlers)
    original_level = root.level
    root.setLevel(logging.ERROR)
    session = ErrorLogSession(tmp_path)
    try:
        with pytest.raises(RuntimeError, match="caller failure"):
            with session:
                handler = _file_handler()
                stream = handler.stream
                assert stream is not None
                raise RuntimeError("caller failure")
        assert stream is not None
        assert stream.closed
        assert handler.stream is None
        assert root.handlers == handlers_before
        assert root.level == logging.ERROR
        session.close()
        session.close()
        assert root.handlers == handlers_before
    finally:
        root.setLevel(original_level)


def test_default_user_data_works_for_frozen_application(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A frozen/read-only install writes beside scores in writable XDG data."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "userdata"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    with ErrorLogSession() as session:
        assert session.path == (
            tmp_path / "userdata" / "forty-two-pacman" / "errors.log"
        )
        LOGGER.error("packaged application")
    assert session.path is not None
    assert "packaged application" in session.path.read_text()


def test_missing_or_relative_xdg_uses_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same safe home fallback is used when XDG is missing or relative."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    expected = tmp_path / ".local/share/forty-two-pacman/errors.log"
    for value in (None, "relative/path"):
        if value is None:
            monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        else:
            monkeypatch.setenv("XDG_DATA_HOME", value)
        with ErrorLogSession() as session:
            assert session.path == expected
    assert expected.is_file()


def test_same_active_session_does_not_duplicate_handlers(
    tmp_path: Path,
) -> None:
    """Repeated entry into one active session cannot attach handlers twice."""
    session = ErrorLogSession(tmp_path)
    try:
        assert session.__enter__() is session
        handlers = list(logging.getLogger().handlers)
        assert session.__enter__() is session
        assert logging.getLogger().handlers == handlers
    finally:
        session.close()


@pytest.mark.parametrize("basename", ["errors.log", "errors.log.1"])
def test_active_config_alias_survives_writes_and_rotation(
    tmp_path: Path, basename: str,
) -> None:
    """Neither a primary log nor its backup may overwrite an active config."""
    config = tmp_path / basename
    original = b'{"lives": 3, "note": "configuration must survive"}\n'
    config.write_bytes(original)
    alias = tmp_path / "active-settings"
    alias.symlink_to(config)
    with ErrorLogSession(
        tmp_path, max_bytes=240, protected_paths=(alias,),
    ) as session:
        assert session.path == tmp_path / "errors-2.log"
        for number in range(30):
            LOGGER.info("protected input rotation %02d %s", number, "x" * 40)
    assert config.read_bytes() == original
    assert alias.read_bytes() == original
    assert (tmp_path / "errors-2.log.3").is_file()
    assert len(list(tmp_path.glob("errors-2.log*"))) == 4


def test_unrelated_config_keeps_standard_log_path(tmp_path: Path) -> None:
    """Protecting an ordinary config does not rename the usual error log."""
    config = tmp_path / "config.json"
    config.write_text('{"lives": 3}')
    with ErrorLogSession(tmp_path, protected_paths=(config,)) as session:
        assert session.path == tmp_path / "errors.log"
        LOGGER.info("ordinary configuration")
    assert config.read_text() == '{"lives": 3}'


def test_alternate_log_checks_its_backups_too(tmp_path: Path) -> None:
    """A second collision advances until the complete rotation set is safe."""
    first = tmp_path / "errors.log"
    second = tmp_path / "errors-2.log.3"
    first.write_text("first protected input")
    second.write_text("second protected input")
    with ErrorLogSession(
        tmp_path, protected_paths=(first, second),
    ) as session:
        assert session.path == tmp_path / "errors-3.log"
    assert first.read_text() == "first protected input"
    assert second.read_text() == "second protected input"


def test_path_resolution_failure_keeps_console_available(
    tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    """Unreadable path aliases cannot escape the console fallback boundary."""
    config = tmp_path / "config"
    with patch("pathlib.Path.resolve", side_effect=OSError("resolve denied")):
        with ErrorLogSession(tmp_path, protected_paths=(config,)) as session:
            assert session.path is None
            assert "resolve denied" in session.warning
            LOGGER.error("console after path failure")
    console = capsys.readouterr().err
    assert "console after path failure" in console
    assert "Traceback" not in console
    assert not list(tmp_path.glob("errors*.log"))
