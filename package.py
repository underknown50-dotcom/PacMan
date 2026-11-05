"""Automated packaging script for Chapter 7 project delivery.

Builds a standalone executable using PyInstaller and packages it into
a release directory along with config.json and INSTRUCTIONS.txt ready
for distribution on Itch.io or Steam.
"""

import os
import shutil
import subprocess
import sys


def build_package() -> None:
    """Execute PyInstaller build and bundle release distribution."""
    print("=" * 60)
    print("Building 42 Pac-Man Standalone Release Package")
    print("=" * 60)

    # 1. Ensure pyinstaller is available
    import importlib.util

    if importlib.util.find_spec("PyInstaller") is None:
        print("[Build] Installing PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"]
        )

    data_sep = ":" if os.name != "nt" else ";"
    data_flag = f"--add-data=config.json{data_sep}."

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=pac-man",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        data_flag,
        "pac-man.py",
    ]

    print(f"[Build] Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    # 3. Create release folder
    dist_dir = os.path.join("dist", "pac-man")
    os.makedirs(dist_dir, exist_ok=True)

    # Copy config.json to dist
    shutil.copy("config.json", os.path.join(dist_dir, "config.json"))

    # Create in-package instructions
    instructions_path = os.path.join(dist_dir, "INSTRUCTIONS.txt")
    with open(instructions_path, "w", encoding="utf-8") as f:
        f.write(
            "42 PAC-MAN - IN-PACKAGE INSTRUCTIONS\n"
            "====================================\n\n"
            "1. LAUNCHING THE GAME:\n"
            "   - Direct / double-click: auto-loads bundled config.json\n"
            "   - Terminal launch: ./pac-man config.json\n\n"
            "2. CONTROLS:\n"
            "   - Arrow Keys / WASD : Move Pac-Man\n"
            "   - P                 : Pause / Resume game\n"
            "   - ESC               : Exit or Return to menu\n\n"
            "3. CHEAT HOTKEYS (Reviewer Mode):\n"
            "   - I : Toggle Invincibility (never lose lives)\n"
            "   - L : Skip current level\n"
            "   - F : Freeze all ghosts\n"
            "   - + : Add extra life\n"
            "   - S : Speed boost\n\n"
            "4. CONFIGURATION:\n"
            "   Modify 'config.json' to change starting lives, points,\n"
            "   and maze dimensions for each level.\n"
        )

    print("\n[Build Success] Packaged release built in:")
    print(f"  {os.path.abspath(dist_dir)}")
    print("Ready for upload to Itch.io / Steam!")


if __name__ == "__main__":
    build_package()
