"""Remove only known build caches, preserving sources and all user data."""

from pathlib import Path
import shutil


def main() -> None:
    """Delete explicitly scoped caches, without following source symlinks."""
    root = Path(__file__).resolve().parent.parent
    for name in ("build", ".mypy_cache", ".pytest_cache"):
        path = root / name
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
    for folder in (root / "pacman", root / "dev_tests", root / "tools"):
        for path in folder.rglob("__pycache__"):
            if not path.is_symlink():
                shutil.rmtree(path)
    cache = root / "__pycache__"
    if cache.is_dir() and not cache.is_symlink():
        shutil.rmtree(cache)
    print("Removed build caches. Scores, archives, wheels and releases kept.")


if __name__ == "__main__":
    main()
