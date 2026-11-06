"""Check configuration repairs, ordinary JSON and secure path handling."""

import json
import logging
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

from pacman.configuration import (
    ConfigurationError, DEFAULT_LEVELS, GameConfig, load_config,
    resolve_highscore_path,
)


def write_config(tmp_path: Path, value: object) -> Path:
    """Write a JSON configuration value into a temporary directory."""
    path = tmp_path / "settings.custom"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_default_config_is_complete() -> None:
    """The shipped config has all fields and ten intended defaults."""
    path = Path(__file__).resolve().parents[1] / "config.json"
    config = load_config(path)
    assert [(level.width, level.height) for level in config.levels] == [
        (level.width, level.height) for level in GameConfig().levels
    ]
    assert [level.level_max_time for level in config.levels] == [
        180, 180, 210, 240, 240, 270, 300, 330, 360, 400,
    ]
    assert config.lives == 3 and config.pellet_coverage == .8
    assert len(DEFAULT_LEVELS) == 10


def test_comment_example_is_valid() -> None:
    """The shipped example accepts comments and its final time override."""
    path = Path(__file__).resolve().parents[1] / "config.comments.json"
    config = load_config(path)
    assert len(config.levels) == 10
    assert config.levels[-1].level_max_time == 400


def test_hash_in_string_and_non_json_extension(tmp_path: Path) -> None:
    """Comments never strip literal hashes or require a .json suffix."""
    path = tmp_path / "settings.anything"
    path.write_text(
        '  # comment\n{\n"note": "keep # inside",\n'
        '# another comment\n"lives": 5\n}\n', encoding="utf-8",
    )
    assert load_config(path).lives == 5


def test_missing_fields_warn_and_recover(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    """Empty settings recover the full defaults with visible warnings."""
    with caplog.at_level(logging.WARNING):
        result = load_config(write_config(tmp_path, {}))
    assert result == GameConfig()
    assert "lives" in caplog.text
    assert "at least ten" in caplog.text


@pytest.mark.parametrize("raw", ["[]", "null", "true", "42", '"hello"'])
def test_wrong_json_root(tmp_path: Path, raw: str) -> None:
    """A complete configuration file must contain a JSON object."""
    path = tmp_path / "config"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ConfigurationError, match="JSON object"):
        load_config(path)


@pytest.mark.parametrize("raw", ["", "{", '{"lives":3,}', "# only comment"])
def test_broken_json_is_clear(tmp_path: Path, raw: str) -> None:
    """Broken whole-file JSON raises the expected readable boundary error."""
    path = tmp_path / "broken"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid JSON"):
        load_config(path)


def test_missing_config_is_clear(tmp_path: Path) -> None:
    """A missing file is distinct from recoverable individual fields."""
    with pytest.raises(ConfigurationError, match="Cannot read"):
        load_config(tmp_path / "missing.json")


def test_unreadable_config_is_clear(tmp_path: Path) -> None:
    """An unreadable file reports a configuration error without a traceback."""
    with patch("pathlib.Path.open", side_effect=PermissionError("denied")):
        with pytest.raises(ConfigurationError, match="Cannot read"):
            load_config(tmp_path / "unreadable.json")


def test_invalid_encoding_is_clear(tmp_path: Path) -> None:
    """Invalid UTF-8 data cannot escape the configuration error boundary."""
    path = tmp_path / "bad.json"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(ConfigurationError, match="Cannot read"):
        load_config(path)


def test_utf8_bom_is_allowed(tmp_path: Path) -> None:
    """Files saved with a UTF-8 BOM remain usable."""
    path = tmp_path / "bom.json"
    path.write_text('{"lives": 7}', encoding="utf-8-sig")
    assert load_config(path).lives == 7


@pytest.mark.parametrize("value", [True, False, "9", 3.0, None, [], {}])
def test_invalid_integer_type_uses_default(
    tmp_path: Path, value: object,
) -> None:
    """Booleans and other non-integers cannot masquerade as numeric fields."""
    assert load_config(write_config(tmp_path, {"lives": value})).lives == 3


@pytest.mark.parametrize("value", [True, False, "9", None, [], {}])
def test_invalid_float_type_uses_default(
    tmp_path: Path, value: object,
) -> None:
    """Speed settings reject booleans, strings and containers."""
    config = load_config(write_config(tmp_path, {"player_speed": value}))
    assert config.player_speed == 5.0


def test_bounds_are_clamped(tmp_path: Path) -> None:
    """Unsafe magnitudes are repaired to documented usable limits."""
    config = load_config(write_config(tmp_path, {
        "lives": -1, "pacgum": 99999, "points_per_pacgum": -2,
        "points_per_super_pacgum": 9999999, "points_per_ghost": -1,
        "seed": 0, "level_max_time": 0, "power_duration": 100,
        "ghost_respawn_delay": 0, "player_speed": 100,
        "ghost_speed": -1, "pellet_coverage": 0.1,
        "levels": [{"width": 0, "height": 100, "level_max_time": 9999}],
    }))
    assert config.lives == 1
    assert config.pacgum == 2000
    assert config.points_per_pacgum == 0
    assert config.points_per_super_pacgum == 1_000_000
    assert config.points_per_ghost == 0
    assert config.seed == 1
    assert config.level_max_time == 10.0
    assert config.power_duration == 60.0
    assert config.ghost_respawn_delay == 5.0
    assert config.player_speed == 15.0
    assert config.ghost_speed == 0.5
    assert config.pellet_coverage == 0.65
    assert config.levels[0].width == 15
    assert config.levels[0].height == 35
    assert config.levels[0].level_max_time == 3600.0


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_numbers_recover(tmp_path: Path, value: float) -> None:
    """Nonstandard JSON non-finite numbers are replaced with safe defaults."""
    config = load_config(write_config(tmp_path, {"player_speed": value}))
    assert config.player_speed == 5.0


def test_huge_numeric_values_do_not_overflow(tmp_path: Path) -> None:
    """Very large parsed integers are clamped before conversion to float."""
    config = load_config(write_config(tmp_path, {"player_speed": 10**500}))
    assert config.player_speed == 15.0


@pytest.mark.parametrize("levels", [None, True, {}, "ten", [], [None, True]])
def test_invalid_or_short_levels_repair(
    tmp_path: Path, levels: object,
) -> None:
    """Every parsed configuration retains ten safe levels."""
    config = load_config(write_config(tmp_path, {"levels": levels}))
    assert len(config.levels) == 10
    assert all(15 <= level.width <= 35 for level in config.levels)


def test_level_time_inheritance_and_even_dimensions(tmp_path: Path) -> None:
    """Per-level timers override the global value and even sizes are legal."""
    config = load_config(write_config(tmp_path, {
        "level_max_time": 123,
        "levels": [
            {"width": 20, "height": 20},
            {"width": True, "height": None, "level_max_time": 45},
        ],
    }))
    assert (config.levels[0].width, config.levels[0].height) == (20, 20)
    assert config.levels[0].level_max_time == 123
    assert config.levels[1].level_max_time == 45
    assert config.levels[9].level_max_time == 123


def test_level_count_has_generous_upper_bound(tmp_path: Path) -> None:
    """Gigantic level lists are bounded without dropping below ten."""
    levels = [{"width": 19, "height": 17}] * 110
    config = load_config(write_config(tmp_path, {"levels": levels}))
    assert len(config.levels) == 100


def test_defense_time_changes_are_reloaded(tmp_path: Path) -> None:
    """Reloading edited settings updates values without source changes."""
    path = write_config(tmp_path, {"lives": 4, "unknown": "ignored"})
    assert load_config(path).lives == 4
    path.write_text('{"lives": 8}', encoding="utf-8")
    assert load_config(path).lives == 8


@pytest.mark.parametrize("filename", [
    "../scores.json", "nested/../../scores.json", "/etc/scores.json",
    "C:/scores.json", "nested\\scores.json", "", "scores.txt",
    "scores.json/", "nested//scores.json", "./scores.json",
    ".git/scores.json", "@userdata/../scores.json", "bad\x00.json",
])
def test_unsafe_score_paths_rejected(tmp_path: Path, filename: str) -> None:
    """Traversal, system paths and non-JSON filenames never become writes."""
    with pytest.raises(ConfigurationError):
        resolve_highscore_path(filename, tmp_path / "config.json")
    config = load_config(write_config(tmp_path, {
        "highscore_filename": filename,
    }))
    assert config.highscore_filename == "@userdata/highscores.json"


def test_relative_score_path(tmp_path: Path) -> None:
    """Source runs resolve nested relative paths beside the configuration."""
    resolved = resolve_highscore_path("scores/top.json", tmp_path / "config")
    assert resolved == tmp_path / "scores" / "top.json"


def test_userdata_score_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit user data paths honor XDG_DATA_HOME."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    resolved = resolve_highscore_path(
        "@userdata/highscores.json", Path("config"),
    )
    expected = tmp_path / "xdg" / "forty-two-pacman" / "highscores.json"
    assert resolved == expected


def test_packaged_score_path_redirects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Frozen builds never attempt writes beside read-only installed assets."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    resolved = resolve_highscore_path(
        "scores/top.json", Path("/opt/game/config"),
    )
    expected = tmp_path / "xdg" / "forty-two-pacman" / "scores/top.json"
    assert resolved == expected


def test_score_path_rejects_symlink_escape(tmp_path: Path) -> None:
    """A directory symlink cannot redirect score writes outside their base."""
    base = tmp_path / "base"
    base.mkdir()
    (base / "escape").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ConfigurationError, match="escapes"):
        resolve_highscore_path("escape/scores.json", base / "config")


def test_score_path_rejects_protected_root() -> None:
    """A config in a protected system directory cannot authorize its writes."""
    with pytest.raises(ConfigurationError, match="system directory"):
        resolve_highscore_path("scores.json", Path("/etc/game/config.json"))


def test_scores_cannot_overwrite_active_config(tmp_path: Path) -> None:
    """A valid-looking relative score filename cannot target its own config."""
    path = tmp_path / 'settings.json'
    path.write_text('{"highscore_filename": "settings.json"}',
                    encoding='utf-8')
    with pytest.raises(ConfigurationError, match='overwrite'):
        resolve_highscore_path('settings.json', path)
    config = load_config(path)
    assert config.highscore_filename == '@userdata/highscores.json'
    assert 'settings.json' in path.read_text(encoding='utf-8')
