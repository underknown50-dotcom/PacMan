# -*- mode: python ; coding: utf-8 -*-
"""Build a Linux folder containing the game and its Python runtime."""

from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata


project_root = Path(SPECPATH)
runtime_data = [
    (str(project_root / "config.json"), "."),
    (str(project_root / "PLAYER_GUIDE.txt"), "."),
]
runtime_data += copy_metadata("mazegenerator")

analysis = Analysis(
    [str(project_root / "pac-man.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=runtime_data,
    hiddenimports=["mazegenerator", "mazegenerator.mazegenerator"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "mypy", "flake8", "dev_tests"],
    noarchive=False,
    optimize=0,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="pacman42",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)
collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="pacman42",
)
