"""Opt-in release diagnostic: exercise the same application and real window."""

from __future__ import annotations

from collections import deque
import json
from pathlib import Path
import os
from typing import cast

from pacman.app import App
from pacman.graphics import InputEvent
from pacman.maze_adapter import Cell, Direction, Maze
from pacman.models import State


def _route(maze: Maze, start: Cell, goal: Cell) -> list[Cell]:
    """Find an existing passage route for the diagnostic's automated player."""
    previous: dict[Cell, Cell | None] = {start: None}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for neighbor in maze.neighbors(current):
            if neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)
    route = [goal]
    while route[-1] != start:
        parent = previous[route[-1]]
        assert parent is not None
        route.append(parent)
    return list(reversed(route))[1:]


def exercise(app: App) -> None:
    """Verify a real clear, ten-level victory, loss, saving and menu reuse.

    Enabled only by PACMAN_SMOKE_TEST=1. No sleeps or network access are used.
    Set XDG_DATA_HOME to a temporary directory to isolate diagnostic scores.
    """
    screenshots = os.environ.get("PACMAN_SCREENSHOTS")

    def frame(label: str) -> None:
        """Render and optionally capture a screen using the real frontend."""
        app.draw()
        if screenshots:
            folder = Path(screenshots)
            folder.mkdir(parents=True, exist_ok=True)
            app.graphics.save_screenshot(folder / f"{label}.png")

    def key(value: str) -> None:
        """Route the same normalized key object as native keyboard input."""
        app.handle(InputEvent("key", key=value))

    try:
        assert app.page == "main"
        frame("01-main-menu")
        key("enter")
        assert app.game.state == State.PLAYING
        game = app.game
        frame("02-playing")
        key("p")
        timer = game.time_left
        app.update(2)
        assert game.state.value == "paused" and game.time_left == timer
        frame("03-pause")
        key("p")
        key("f1")
        key("g")
        key("i")
        game.time_left = 3600  # Diagnostic time budget for a complete route.
        key("o")
        eaten = game.ghosts[0]
        eaten.reset(game.player.cell)
        app.update(game.STEP)
        assert not eaten.active and eaten.returning
        captured_score = game.score
        key("g")
        app.update(.12)
        assert eaten.returning and not eaten.active
        frame("02b-returning-eyes")
        while eaten.returning:
            app.update(game.STEP)
        assert eaten.cell == eaten.home and not eaten.active
        assert game.score >= captured_score
        frame("02c-eyes-home")
        key("g")
        original_count = len(game.pellets) + len(game.powers)
        while game.state == State.PLAYING:
            remaining = game.pellets | game.powers
            assert remaining
            distances = game.maze.distances(game.player.cell)
            goal = min(remaining, key=lambda cell: (distances[cell], cell))
            for destination in _route(game.maze, game.player.cell, goal):
                delta = (destination[0] - game.player.cell[0],
                         destination[1] - game.player.cell[1])
                direction = next(d for d in Direction if d.delta == delta)
                game.set_direction(direction)
                game.update(1.0 / game.config.player_speed)
                assert game.player.cell == destination
                if game.state != State.PLAYING:
                    break
        assert game.state.value == "transition" and game.score > 0
        frame("04-level-cleared")
        game.update(1.6)
        for index in range(1, len(game.config.levels)):
            assert game.level_index == index
            key("n")
            if index < len(game.config.levels) - 1:
                game.update(1.6)
        assert cast(str, game.state.value) == "victory"
        frame("05-victory")
        app.handle(InputEvent("text", text="REVIEW42"))
        key("enter")
        assert app.page == "main"
        assert any(entry.name == "REVIEW42" for entry in app.scores.entries)
        app.scores.load()
        assert any(entry.name == "REVIEW42" for entry in app.scores.entries)
        key("enter")
        key("f1")
        key("t")
        app.update(1.1)
        assert game.state == State.GAME_OVER
        frame("06-game-over")
        key("escape")  # Explicit default-name save.
        assert app.page == "main"
        key("down")
        key("enter")
        assert app.page == "highscores"
        frame("07-highscores")
        key("escape")
        key("down")
        key("enter")
        assert app.page == "instructions"
        frame("08-instructions")
        key("escape")
        app.handle(InputEvent("quit"))
        assert not app.running
        print(json.dumps({"smoke": "passed", "levels": len(game.config.levels),
                          "first_level_collectibles": original_count,
                          "persisted_entries": len(app.scores.entries)}))
    finally:
        app.graphics.close()
