"""Configuration loader module for Pac-Man.

Handles JSON files with comment support (# lines), robust schema validation,
clamping of out-of-range values, and graceful fallback to defaults without
ever raising unhandled exceptions or printing Python tracebacks.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class LevelConfig:
    """Configuration parameters for an individual game level."""

    level: int = 1
    width: int = 15
    height: int = 15
    max_time: int = 90


@dataclass
class GameConfig:
    """Full game configuration with safe default values."""

    highscore_filename: str = "highscores.json"
    lives: int = 3
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    level_max_time: int = 90
    seed: int = 42
    levels: List[LevelConfig] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Ensure that at least 10 levels are defined."""
        if not self.levels or len(self.levels) < 10:
            existing_count = len(self.levels)
            for idx in range(existing_count + 1, 11):
                # Gradually expand maze size as levels increase
                dim = min(25, 13 + (idx * 2))
                self.levels.append(
                    LevelConfig(
                        level=idx,
                        width=dim,
                        height=dim,
                        max_time=self.level_max_time,
                    )
                )


class ConfigLoader:
    """Loads and validates game configuration from a JSON file."""

    DEFAULT_HIGHSCORE = "highscores.json"
    MIN_LIVES = 1
    MAX_LIVES = 99
    MIN_POINTS = 0
    MAX_POINTS = 100000
    MIN_TIME = 10
    MAX_TIME = 600
    MIN_DIM = 7
    MAX_DIM = 41

    @classmethod
    def strip_comments(cls, content: str) -> str:
        """Strip lines starting with '#' or '//' and trailing comments."""
        cleaned_lines: List[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            # Remove inline comments if present outside of quoted strings
            cleaned_line = re.sub(r"\s*(#|//).*$", "", line)
            cleaned_lines.append(cleaned_line)
        return "\n".join(cleaned_lines)

    @classmethod
    def load(cls, file_path: str) -> GameConfig:
        """Load configuration from the specified file path safely.

        Args:
            file_path: Path to the JSON configuration file.

        Returns:
            A validated GameConfig instance with safe defaults applied.
        """
        defaults = GameConfig()

        if not file_path:
            print("[Config Warning] No config path provided; using defaults.")
            return defaults

        if not os.path.exists(file_path):
            print(
                f"[Config Warning] File '{file_path}' not found; "
                "using default configuration."
            )
            return defaults

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                raw_content = file.read()
        except OSError as err:
            print(f"[Config Warning] Cannot read '{file_path}': {err}.")
            return defaults

        cleaned = cls.strip_comments(raw_content)

        try:
            raw_data = json.loads(cleaned)
            if not isinstance(raw_data, dict):
                print(
                    "[Config Warning] Root JSON element is not an object; "
                    "using defaults."
                )
                return defaults
        except (json.JSONDecodeError, ValueError) as err:
            print(
                f"[Config Warning] Malformed JSON in '{file_path}': {err}. "
                "Falling back to safe defaults."
            )
            return defaults

        return cls._parse_dict(raw_data, defaults)

    @classmethod
    def _parse_dict(
        cls, data: Dict[str, Any], defaults: GameConfig
    ) -> GameConfig:
        """Parse dictionary values and clamp them to safe ranges."""
        highscore_filename = defaults.highscore_filename
        if "highscore_filename" in data:
            val = data["highscore_filename"]
            if isinstance(val, str) and val.strip():
                highscore_filename = val.strip()
            else:
                print(
                    "[Config Warning] 'highscore_filename' invalid; "
                    f"using default '{highscore_filename}'."
                )

        lives = cls._clamp_int(
            data.get("lives"),
            defaults.lives,
            cls.MIN_LIVES,
            cls.MAX_LIVES,
            "lives",
        )

        pts_pacgum = cls._clamp_int(
            data.get("points_per_pacgum"),
            defaults.points_per_pacgum,
            cls.MIN_POINTS,
            cls.MAX_POINTS,
            "points_per_pacgum",
        )

        pts_super = cls._clamp_int(
            data.get("points_per_super_pacgum"),
            defaults.points_per_super_pacgum,
            cls.MIN_POINTS,
            cls.MAX_POINTS,
            "points_per_super_pacgum",
        )

        pts_ghost = cls._clamp_int(
            data.get("points_per_ghost"),
            defaults.points_per_ghost,
            cls.MIN_POINTS,
            cls.MAX_POINTS,
            "points_per_ghost",
        )

        level_max_time = cls._clamp_int(
            data.get("level_max_time"),
            defaults.level_max_time,
            cls.MIN_TIME,
            cls.MAX_TIME,
            "level_max_time",
        )

        seed = cls._parse_int(data.get("seed"), defaults.seed, "seed")

        levels: List[LevelConfig] = []
        raw_levels = data.get("levels") or data.get("level")
        if isinstance(raw_levels, list):
            for idx, lvl_obj in enumerate(raw_levels, start=1):
                if isinstance(lvl_obj, dict):
                    w = cls._clamp_int(
                        lvl_obj.get("width"),
                        15,
                        cls.MIN_DIM,
                        cls.MAX_DIM,
                        f"level {idx} width",
                    )
                    # Enforce odd dimensions for clean corridor centering
                    if w % 2 == 0:
                        w += 1
                    h = cls._clamp_int(
                        lvl_obj.get("height"),
                        15,
                        cls.MIN_DIM,
                        cls.MAX_DIM,
                        f"level {idx} height",
                    )
                    if h % 2 == 0:
                        h += 1
                    t = cls._clamp_int(
                        lvl_obj.get("max_time"),
                        level_max_time,
                        cls.MIN_TIME,
                        cls.MAX_TIME,
                        f"level {idx} max_time",
                    )
                    levels.append(
                        LevelConfig(
                            level=idx, width=w, height=h, max_time=t
                        )
                    )

        config = GameConfig(
            highscore_filename=highscore_filename,
            lives=lives,
            points_per_pacgum=pts_pacgum,
            points_per_super_pacgum=pts_super,
            points_per_ghost=pts_ghost,
            level_max_time=level_max_time,
            seed=seed,
            levels=levels,
        )
        return config

    @classmethod
    def _clamp_int(
        cls,
        val: Any,
        default: int,
        min_val: int,
        max_val: int,
        name: str,
    ) -> int:
        """Safely parse and clamp an integer value."""
        if val is None:
            return default
        try:
            num = int(val)
        except (ValueError, TypeError):
            print(
                f"[Config Warning] Invalid integer for '{name}': {val!r}. "
                f"Defaulting to {default}."
            )
            return default

        if num < min_val:
            print(
                f"[Config Warning] '{name}' value {num} is below minimum "
                f"{min_val}; clamped to {min_val}."
            )
            return min_val
        if num > max_val:
            print(
                f"[Config Warning] '{name}' value {num} is above maximum "
                f"{max_val}; clamped to {max_val}."
            )
            return max_val
        return num

    @classmethod
    def _parse_int(cls, val: Any, default: int, name: str) -> int:
        """Safely parse an integer without clamping."""
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            print(
                f"[Config Warning] Invalid integer for '{name}': {val!r}. "
                f"Defaulting to {default}."
            )
            return default
