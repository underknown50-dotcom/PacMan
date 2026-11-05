# 🛠️ Developer Scripts & Exploration Utilities

This directory contains utility scripts developed during early sprint phases to inspect external dependencies and verify display environments.

---

## 📜 Utilities Overview

1. **`test_generator.py`**:
   - Inspects the assigned `mazegenerator-2.1.0-py3-none-any.whl` binary package.
   - Generates an ASCII representation of the maze in terminal to visualize corridor loops and bitmask wall values (`perfect=False`, `seed=42`).
   - **Usage:**
     ```bash
     python3 scripts/test_generator.py
     ```

2. **`test_window.py`**:
   - Minimal graphics harness testing SDL2 display initialization, 60 FPS clock ticking, and keyboard event handling.
   - **Usage:**
     ```bash
     python3 scripts/test_window.py
     ```
