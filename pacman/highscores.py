"""Validate, rank and atomically persist the ten best completed runs."""

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import re
import tempfile


LOGGER = logging.getLogger(__name__)
_NAME_PATTERN = re.compile(r"[A-Za-z0-9 ]{1,10}\Z")


@dataclass(frozen=True)
class ScoreEntry:
    """Store a printable player name and a non-negative integer score."""

    name: str
    score: int


def validate_name(name: str) -> bool:
    """Accept at most ten ASCII letters, digits or spaces with visible text."""
    return bool(_NAME_PATTERN.fullmatch(name)) and bool(name.strip())


class HighScoreStore:
    """Keep a usable in-memory leaderboard when persistence is unavailable."""

    def __init__(self, path: Path) -> None:
        """Create an empty store whose reads and writes use the given path."""
        self.path = path
        self.entries: list[ScoreEntry] = []
        self.last_warning = ""

    def _warn(self, message: str) -> None:
        """Keep the latest recoverable problem available to the interface."""
        self.last_warning = message
        LOGGER.warning("%s", message)

    def load(self) -> None:
        """Read valid records, tolerating missing or damaged files."""
        self.last_warning = ""
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                records: object = json.load(stream)
        except FileNotFoundError:
            self.entries = []
            return
        except (OSError, UnicodeError, ValueError, RecursionError) as error:
            self._warn(f"Cannot load highscores: {error}")
            return
        if not isinstance(records, list):
            self._warn("Highscores must contain a JSON array; ignoring file")
            return
        valid: list[ScoreEntry] = []
        invalid = 0
        for record in records:
            if not isinstance(record, dict):
                invalid += 1
                continue
            name: object = record.get("name")
            score: object = record.get("score")
            if (
                not isinstance(name, str) or not validate_name(name)
                or isinstance(score, bool) or not isinstance(score, int)
                or score < 0
            ):
                invalid += 1
                continue
            valid.append(ScoreEntry(name.strip(), score))
        # Stable sorting keeps older records first when scores are tied.
        self.entries = sorted(valid, key=lambda entry: -entry.score)[:10]
        if invalid:
            self._warn(f"Ignored {invalid} invalid highscore record(s)")

    def add(self, name: str, score: int) -> bool:
        """Add a validated run in memory and retain the ten best scores."""
        self.last_warning = ""
        if not validate_name(name):
            self._warn(
                "Use 1-10 ASCII letters, digits or spaces; no blank name"
            )
            return False
        if isinstance(score, bool) or not isinstance(score, int) or score < 0:
            self._warn("A highscore must be a non-negative integer")
            return False
        self.entries.append(ScoreEntry(name.strip(), score))
        self.entries.sort(key=lambda entry: -entry.score)
        self.entries = self.entries[:10]
        return True

    def save(self) -> bool:
        """Atomically replace the JSON file and tolerate write errors."""
        self.last_warning = ""
        temporary: Path | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent,
                prefix=".highscores-", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(
                    [{"name": item.name, "score": item.score}
                     for item in self.entries],
                    stream, indent=2, ensure_ascii=True,
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        except (OSError, ValueError) as error:
            self._warn(f"Cannot save highscores (kept in memory): {error}")
            return False
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
        return True
