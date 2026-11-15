"""Load recoverable JSON settings and resolve safe writable score paths."""

from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys


LOGGER = logging.getLogger(__name__)
DEFAULT_SCORE_FILE = "@userdata/highscores.json"
DEFAULT_GHOST_SPEED = 1.5
DATA_DIRECTORY = "forty-two-pacman"
MIN_LEVELS = 10
MAX_LEVELS = 100
_SAFE_COMPONENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_. -]*\Z")
_PROTECTED_ROOTS = (
    "/bin", "/boot", "/dev", "/etc", "/lib", "/lib64", "/proc",
    "/run", "/sbin", "/sys", "/usr",
)


class ConfigurationError(Exception):
    """Describe an unusable configuration file or unsafe storage path."""


@dataclass(frozen=True)
class LevelConfig:
    """Store the maze dimensions and countdown for one playable level."""

    width: int
    height: int
    level_max_time: float = 180.0


DEFAULT_LEVELS = tuple(
    LevelConfig(width, height)
    for width, height in (
        (19, 17), (19, 17), (21, 17), (21, 19), (21, 19),
        (23, 19), (23, 21), (25, 21), (25, 23), (27, 23),
    )
)


@dataclass(frozen=True)
class GameConfig:
    """Provide immutable validated settings shared by the game components."""

    levels: tuple[LevelConfig, ...] = DEFAULT_LEVELS
    lives: int = 3
    pacgum: int = 42
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: float = 180.0
    power_duration: float = 8.0
    ghost_respawn_delay: float = 7.0
    player_speed: float = 5.0
    ghost_speed: float = DEFAULT_GHOST_SPEED
    pellet_coverage: float = 0.8
    highscore_filename: str = DEFAULT_SCORE_FILE


def _integer(
    data: dict[str, object], key: str, default: int,
    minimum: int, maximum: int, context: str = "configuration",
) -> int:
    """Read an integer, defaulting invalid types and clamping its range."""
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        LOGGER.warning(
            "%s.%s is missing or not an integer; using %s",
            context, key, default,
        )
        return default
    result = max(minimum, min(maximum, value))
    if result != value:
        LOGGER.warning(
            "%s.%s must be %s..%s; clamped to %s",
            context, key, minimum, maximum, result,
        )
    return result


def _number(
    data: dict[str, object], key: str, default: float,
    minimum: float, maximum: float, context: str = "configuration",
) -> float:
    """Read a finite number with type defaults and range clamping."""
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        LOGGER.warning(
            "%s.%s is missing or not a number; using %s",
            context, key, default,
        )
        return default
    if isinstance(value, float) and not math.isfinite(value):
        LOGGER.warning(
            "%s.%s must be finite; using %s", context, key, default,
        )
        return default
    # Compare before conversion so extremely large JSON integers stay safe.
    bounded = max(minimum, min(maximum, value))
    if bounded != value:
        LOGGER.warning(
            "%s.%s must be %s..%s; clamped to %s",
            context, key, minimum, maximum, bounded,
        )
    return float(bounded)


def _object(value: object) -> dict[str, object] | None:
    """Return lowercase-keyed JSON fields or reject a different type."""
    if not isinstance(value, dict):
        return None
    return {
        key.lower(): item for key, item in value.items()
        if isinstance(key, str)
    }


def _levels(data: dict[str, object], time_limit: float) -> tuple[
    LevelConfig, ...
]:
    """Repair level definitions and fill the list to ten playable levels."""
    raw = data.get("levels")
    if not isinstance(raw, list):
        LOGGER.warning("levels is missing or not an array; using ten defaults")
        raw = []
    if len(raw) < MIN_LEVELS:
        LOGGER.warning("levels needs at least ten entries; filling defaults")
    if len(raw) > MAX_LEVELS:
        LOGGER.warning("levels is limited to %s entries", MAX_LEVELS)
    count = max(MIN_LEVELS, min(len(raw), MAX_LEVELS))
    result: list[LevelConfig] = []
    for index in range(count):
        fallback = DEFAULT_LEVELS[min(index, MIN_LEVELS - 1)]
        if index >= len(raw):
            result.append(LevelConfig(
                fallback.width, fallback.height, time_limit,
            ))
            continue
        item = _object(raw[index])
        context = f"levels[{index}]"
        if item is None:
            LOGGER.warning("%s is not an object; using its default", context)
            result.append(LevelConfig(
                fallback.width, fallback.height, time_limit,
            ))
            continue
        result.append(LevelConfig(
            width=_integer(item, "width", fallback.width, 15, 35, context),
            height=_integer(item, "height", fallback.height, 15, 35, context),
            level_max_time=(
                _number(
                    item, "level_max_time", time_limit, 10.0, 3600.0, context,
                ) if "level_max_time" in item else time_limit
            ),
        ))
    return tuple(result)


def _score_parts(filename: str) -> tuple[bool, tuple[str, ...]]:
    """Validate portable relative JSON filenames without hidden components."""
    user_data = filename.startswith("@userdata/")
    relative = filename[len("@userdata/"):] if user_data else filename
    path = PurePosixPath(relative)
    parts = path.parts
    if (
        not relative or len(relative) > 240 or path.is_absolute()
        or "\\" in relative or ":" in relative
        or "//" in relative or relative.endswith("/")
        or not parts or any(
            part in (".", "..") or _SAFE_COMPONENT.fullmatch(part) is None
            for part in relative.split("/")
        )
        or path.suffix.lower() != ".json"
    ):
        raise ConfigurationError(
            "highscore_filename must be a safe relative .json path or "
            "@userdata/<name>.json; absolute paths and traversal are forbidden"
        )
    return user_data, parts


def _user_data_directory() -> Path:
    """Choose the XDG application data directory or its home fallback."""
    configured = os.environ.get("XDG_DATA_HOME", "")
    base = Path(configured).expanduser() if configured else None
    if base is None or not base.is_absolute():
        base = Path.home() / ".local" / "share"
    return base / DATA_DIRECTORY


def resolve_highscore_path(filename: str, config_path: Path) -> Path:
    """Resolve a safe score path, redirecting packaged writes to user data."""
    user_data, parts = _score_parts(filename)
    if user_data or getattr(sys, "frozen", False):
        base = _user_data_directory().resolve()
    else:
        base = config_path.resolve().parent
    destination = base.joinpath(*parts).resolve()
    if not destination.is_relative_to(base):
        raise ConfigurationError(
            "highscore_filename escapes its data directory"
        )
    if destination == config_path.resolve():
        raise ConfigurationError(
            "highscore_filename must not overwrite the configuration file"
        )
    if any(
        destination.is_relative_to(Path(root)) for root in _PROTECTED_ROOTS
    ):
        raise ConfigurationError(
            "highscore_filename targets a system directory"
        )
    return destination


def load_config(path: Path) -> GameConfig:
    """Parse JSON with full-line hash comments and repair individual fields.

    Missing/unreadable files, invalid JSON and non-object roots raise a clear
    ConfigurationError. Field repairs emit logging warnings and retain ten
    or more levels. Unknown fields are deliberately ignored.
    """
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            contents = "".join(
                line for line in stream if not line.lstrip().startswith("#")
            )
        parsed: object = json.loads(contents)
    except (OSError, UnicodeError) as error:
        raise ConfigurationError(
            f"Cannot read configuration '{path}': {error}"
        ) from error
    except (ValueError, RecursionError) as error:
        raise ConfigurationError(
            f"Invalid JSON in configuration '{path}': {error}"
        ) from error
    data = _object(parsed)
    if data is None:
        raise ConfigurationError("Configuration must contain a JSON object")
    time_limit = _number(data, "level_max_time", 180.0, 10.0, 3600.0)
    filename = data.get("highscore_filename")
    if not isinstance(filename, str):
        LOGGER.warning(
            "highscore_filename is missing/invalid; using user data"
        )
        filename = DEFAULT_SCORE_FILE
    else:
        try:
            resolve_highscore_path(filename, path)
        except (ConfigurationError, OSError, RuntimeError) as error:
            LOGGER.warning(
                "Invalid highscore_filename: %s; using user data", error,
            )
            filename = DEFAULT_SCORE_FILE
    return GameConfig(
        levels=_levels(data, time_limit),
        lives=_integer(data, "lives", 3, 1, 99),
        pacgum=_integer(data, "pacgum", 42, 0, 2000),
        points_per_pacgum=_integer(
            data, "points_per_pacgum", 10, 0, 1_000_000,
        ),
        points_per_super_pacgum=_integer(
            data, "points_per_super_pacgum", 50, 0, 1_000_000,
        ),
        points_per_ghost=_integer(
            data, "points_per_ghost", 200, 0, 1_000_000,
        ),
        seed=_integer(data, "seed", 42, 1, 2**31 - 1),
        level_max_time=time_limit,
        power_duration=_number(data, "power_duration", 8.0, 1.0, 60.0),
        ghost_respawn_delay=_number(
            data, "ghost_respawn_delay", 7.0, 5.0, 10.0,
        ),
        player_speed=_number(data, "player_speed", 5.0, 1.0, 15.0),
        ghost_speed=_number(
            data, "ghost_speed", DEFAULT_GHOST_SPEED, 0.5, 12.0,
        ),
        pellet_coverage=_number(data, "pellet_coverage", 0.8, 0.65, 1.0),
        highscore_filename=filename,
    )
