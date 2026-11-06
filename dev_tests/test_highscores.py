"""Check name rules, stable top-ten ranking and recoverable persistence."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pacman.highscores import HighScoreStore, ScoreEntry, validate_name


@pytest.mark.parametrize("name", ["A", "Ada 42", "0123456789", " A "])
def test_valid_names(name: str) -> None:
    """Only printable ASCII letters, digits and spaces are accepted."""
    assert validate_name(name)


@pytest.mark.parametrize("name", [
    "", " ", "          ", "12345678901", "é", "A_B", "A-B", "A\n",
    "A\t", "😀", "日本語", "\x00",
])
def test_invalid_names(name: str) -> None:
    """Blank, overlength, Unicode and punctuation names are rejected."""
    assert not validate_name(name)


def test_missing_file_is_empty(tmp_path: Path) -> None:
    """The first launch begins with an empty usable scoreboard."""
    store = HighScoreStore(tmp_path / "absent.json")
    store.load()
    assert store.entries == []
    assert store.last_warning == ""


def test_ranking_truncation_and_ties(tmp_path: Path) -> None:
    """Only ten entries survive and older equal scores retain precedence."""
    store = HighScoreStore(tmp_path / "scores.json")
    assert store.add("First", 500)
    assert store.add("Second", 500)
    for number in range(20):
        assert store.add(f"P{number}", number)
    assert len(store.entries) == 10
    assert store.entries[:2] == [
        ScoreEntry("First", 500), ScoreEntry("Second", 500),
    ]
    remaining_scores = [entry.score for entry in store.entries[2:]]
    assert remaining_scores == list(range(19, 11, -1))


def test_roundtrip_restart_and_name_trimming(tmp_path: Path) -> None:
    """Atomic saves create parents and survive a new store/application run."""
    path = tmp_path / "nested" / "scores.json"
    first = HighScoreStore(path)
    assert first.add(" Ada ", 100)
    assert first.add("Zero", 0)
    assert first.save()
    second = HighScoreStore(path)
    second.load()
    assert second.entries == [ScoreEntry("Ada", 100), ScoreEntry("Zero", 0)]
    assert json.loads(path.read_text()) == [
        {"name": "Ada", "score": 100}, {"name": "Zero", "score": 0},
    ]
    assert not list(path.parent.glob(".highscores-*.tmp"))


@pytest.mark.parametrize("score", [-1, True, False])
def test_invalid_score_is_rejected(tmp_path: Path, score: int) -> None:
    """Negative scores and bool subclasses cannot enter the ranking."""
    store = HighScoreStore(tmp_path / "scores.json")
    assert not store.add("Ada", score)
    assert store.entries == []
    assert store.last_warning


def test_invalid_name_gives_feedback(tmp_path: Path) -> None:
    """Rejected input leaves existing entries and reports a helpful rule."""
    store = HighScoreStore(tmp_path / "scores.json")
    assert not store.add("bad_name", 2)
    assert "ASCII" in store.last_warning
    assert store.entries == []


@pytest.mark.parametrize("contents", ["{", "null", "{}", '"scores"'])
def test_corrupt_file_retains_memory(tmp_path: Path, contents: str) -> None:
    """Corrupt data cannot crash the game or remove a current valid score."""
    path = tmp_path / "scores.json"
    store = HighScoreStore(path)
    assert store.add("Ada", 42)
    path.write_text(contents, encoding="utf-8")
    store.load()
    assert store.entries == [ScoreEntry("Ada", 42)]
    assert store.last_warning


def test_invalid_records_skipped_and_file_ranked(tmp_path: Path) -> None:
    """Mixed records recover their valid subset with warning and ranking."""
    path = tmp_path / "scores.json"
    records: list[object] = [
        None, [], 5, {"name": "Ada", "score": True},
        {"name": "Ada", "score": -2}, {"name": "Ada", "score": "9"},
        {"name": "é", "score": 4}, {"name": "", "score": 3},
        {"name": "Ada", "score": 5.0}, {"name": "Missing"},
        {"score": 5}, {"name": 5, "score": 4},
    ]
    records.extend({"name": f"P{x}", "score": x} for x in range(20))
    path.write_text(json.dumps(records), encoding="utf-8")
    store = HighScoreStore(path)
    store.load()
    assert [entry.score for entry in store.entries] == list(range(19, 9, -1))
    assert "12 invalid" in store.last_warning


def test_unreadable_file_retains_memory(tmp_path: Path) -> None:
    """Read permission failures preserve usable in-memory scores."""
    store = HighScoreStore(tmp_path / "scores.json")
    assert store.add("Ada", 42)
    with patch("pathlib.Path.open", side_effect=PermissionError("denied")):
        store.load()
    assert store.entries == [ScoreEntry("Ada", 42)]
    assert "Cannot load" in store.last_warning


def test_invalid_encoding_reports_warning(tmp_path: Path) -> None:
    """A non-UTF-8 file is a recoverable storage problem."""
    path = tmp_path / "scores.json"
    path.write_bytes(b"\xff\xfe")
    store = HighScoreStore(path)
    store.load()
    assert store.entries == []
    assert store.last_warning


def test_replace_failure_preserves_disk_and_memory(tmp_path: Path) -> None:
    """Failed atomic replacement leaves the previous file fully intact."""
    path = tmp_path / "scores.json"
    store = HighScoreStore(path)
    assert store.add("Ada", 10)
    assert store.save()
    before = path.read_bytes()
    assert store.add("Next", 20)
    with patch(
        "pacman.highscores.os.replace", side_effect=OSError("disk full"),
    ):
        assert not store.save()
    assert path.read_bytes() == before
    assert store.entries[0] == ScoreEntry("Next", 20)
    assert "kept in memory" in store.last_warning
    assert not list(tmp_path.glob(".highscores-*.tmp"))


def test_unwritable_directory_is_recoverable(tmp_path: Path) -> None:
    """A failure creating the storage directory cannot discard a run."""
    store = HighScoreStore(tmp_path / "nested" / "scores.json")
    assert store.add("Ada", 42)
    with patch("pathlib.Path.mkdir", side_effect=PermissionError("read only")):
        assert not store.save()
    assert store.entries == [ScoreEntry("Ada", 42)]
    assert "Cannot save" in store.last_warning


def test_success_clears_old_warning(tmp_path: Path) -> None:
    """A repaired storage location removes stale warnings after a save."""
    store = HighScoreStore(tmp_path / "scores.json")
    assert not store.add("", 1)
    assert store.add("Ada", 1)
    assert store.last_warning == ""
    assert store.save()
