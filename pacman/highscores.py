"""Persistent highscore system for Pac-Man.

Stores the top 10 highest scores with player names in a local JSON file.
Ensures strict validation of player names (max 10 alphanumeric characters
and spaces) and non-negative integer scores, while gracefully handling any
file corruption, missing files, or I/O errors.
"""

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import List, Tuple


@dataclass
class HighscoreEntry:
    """Represents a single player's score entry."""

    name: str
    score: int

    def to_tuple(self) -> Tuple[str, int]:
        """Convert entry to a (name, score) tuple."""
        return self.name, self.score


class HighscoreManager:
    """Manages reading, updating, and persisting the top 10 highscores."""

    MAX_ENTRIES = 10
    MAX_NAME_LENGTH = 10
    NAME_PATTERN = re.compile(r"^[a-zA-Z0-9 ]{1,10}$")

    def __init__(self, filepath: str = "highscores.json") -> None:
        """Initialize the manager with a target JSON file path."""
        self.filepath = filepath
        self.scores: List[HighscoreEntry] = []
        self.load()

    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """Sanitize and validate player name according to Chapter 5.5.

        Player names must be max 10 characters, alphanumeric and spaces only.
        """
        if not name:
            return "Player"
        # Keep only alphanumeric and spaces
        cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", name).strip()
        if not cleaned:
            return "Player"
        return cleaned[: cls.MAX_NAME_LENGTH]

    def is_valid_name(self, name: str) -> bool:
        """Check if a name strictly matches the required specification."""
        if not name or len(name) > self.MAX_NAME_LENGTH:
            return False
        return bool(self.NAME_PATTERN.match(name))

    def load(self) -> List[HighscoreEntry]:
        """Load highscores from the JSON file on disk.

        Handles missing files, corrupt data, and invalid types cleanly.
        """
        self.scores = []
        if not os.path.exists(self.filepath):
            # Normal on first launch
            return self.scores

        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError, ValueError) as err:
            print(
                f"[Highscore Warning] Cannot read '{self.filepath}': "
                f"{err}. Starting with empty score table."
            )
            return self.scores

        if not isinstance(data, list):
            print(
                "[Highscore Warning] File content is not a list; "
                "resetting highscores."
            )
            return self.scores

        for item in data:
            if isinstance(item, dict):
                raw_name = item.get("name")
                raw_score = item.get("score")
                if isinstance(raw_name, str) and isinstance(raw_score, int):
                    name = self.sanitize_name(raw_name)
                    score = max(0, raw_score)
                    self.scores.append(HighscoreEntry(name=name, score=score))

        self._sort_and_trim()
        return self.scores

    def save(self) -> bool:
        """Save the current top 10 scores to disk.

        Returns:
            True if saving succeeded, False otherwise.
        """
        try:
            self._sort_and_trim()
            payload = [asdict(entry) for entry in self.scores]
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2)
            return True
        except OSError as err:
            print(
                f"[Highscore Warning] Failed to save highscores to "
                f"'{self.filepath}': {err}."
            )
            return False

    def add_score(self, name: str, score: int) -> bool:
        """Add a new score and update the persistent table.

        Args:
            name: Player name string.
            score: Non-negative integer score.

        Returns:
            True if the score made it into the top 10, False otherwise.
        """
        sanitized_name = self.sanitize_name(name)
        safe_score = max(0, int(score))

        entry = HighscoreEntry(name=sanitized_name, score=safe_score)
        self.scores.append(entry)
        self._sort_and_trim()
        self.save()

        # Returns True if the newly added entry remains in the top 10
        return entry in self.scores

    def is_highscore(self, score: int) -> bool:
        """Check if a score qualifies for the top 10."""
        if score <= 0:
            return False
        if len(self.scores) < self.MAX_ENTRIES:
            return True
        return score > self.scores[-1].score

    def get_top_entries(self) -> List[Tuple[str, int]]:
        """Return the top 10 scores as list of (name, score) tuples."""
        return [entry.to_tuple() for entry in self.scores]

    def _sort_and_trim(self) -> None:
        """Sort scores in descending order and keep top 10."""
        self.scores.sort(key=lambda item: item.score, reverse=True)
        self.scores = self.scores[: self.MAX_ENTRIES]
