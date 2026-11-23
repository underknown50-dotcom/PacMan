"""Keyboard-driven application lifecycle around the independent game model."""

from __future__ import annotations

import logging

from pacman.configuration import GameConfig
from pacman.error_logging import ErrorLogSession
from pacman.graphics import Graphics, InputEvent
from pacman.highscores import HighScoreStore
from pacman.maze_adapter import Direction, MazeError
from pacman.models import Game, State
from pacman.rendering import Renderer


DIRECTION_KEYS: dict[str, Direction] = {
    "up": Direction.UP, "w": Direction.UP,
    "right": Direction.RIGHT, "d": Direction.RIGHT,
    "down": Direction.DOWN, "s": Direction.DOWN,
    "left": Direction.LEFT, "a": Direction.LEFT,
}


class App:
    """Coordinate menus, name entry and rendering with explicit transitions."""

    def __init__(self, config: GameConfig, scores: HighScoreStore,
                 log_session: ErrorLogSession | None = None) -> None:
        """Open graphics after configuration and persistent data are loaded."""
        self.game = Game(config)
        self.scores = scores
        self.log_session = log_session
        self.graphics = Graphics()
        try:
            self.renderer = Renderer(self.graphics)
        except BaseException:
            self.graphics.close()
            raise
        self.running = True
        self.page = "main"
        self.selection = 0
        self.pause_selection = 0
        self.confirm_leave = False
        self.name = ""
        self.message = ""
        self.warning = scores.last_warning
        self.error_message = ""
        self._ignore_finish_text = False
        self._finish_trigger_key = ""

    def run(self) -> None:
        """Run the event/update/frame loop and always release the window."""
        try:
            while self.running:
                dt = min(self.graphics.tick(), 0.25)
                for event in self.graphics.events():
                    self.handle(event)
                self.update(dt)
                self.draw()
        finally:
            self.graphics.close()

    def start(self) -> None:
        """Begin a fresh run and show generator failures on a safe screen."""
        self.name = ""
        self.message = ""
        self.confirm_leave = False
        try:
            self.game.start()
            self.page = "game"
        except MazeError as exc:
            self._generation_error(exc)

    def _generation_error(self, error: MazeError) -> None:
        """Explain generation failure and offer a safe return to the menu."""
        logging.getLogger(__name__).exception(
            "Unable to prepare maze: %s", error,
        )
        self.game.return_to_menu()
        self.page = "error"
        self.error_message = str(error)

    def update(self, dt: float) -> None:
        """Advance only the model, handling later-level generation failures."""
        if self.page == "game":
            try:
                self.game.update(dt)
            except MazeError as exc:
                self._generation_error(exc)

    def handle(self, event: InputEvent) -> None:
        """Route a normalized window, key or text event to its screen."""
        if event.kind == "quit":
            self.running = False
            return
        finished = self.game.state in {State.GAME_OVER, State.VICTORY}
        if self.page == "game" and finished:
            if event.kind == "text" and self._ignore_finish_text:
                self._ignore_finish_text = False
                if event.text.lower() == self._finish_trigger_key:
                    return
            if event.kind == "key":
                self._ignore_finish_text = False
            self._name_event(event)
            return
        if event.kind != "key":
            return
        key = event.key
        if self.page == "main":
            self._main_key(key)
        elif self.page in {"instructions", "highscores", "error"}:
            if key in {"escape", "enter", "space"}:
                self.page = "main"
        elif self.page == "game":
            if self.game.state == State.PAUSED:
                self._pause_key(key)
            elif self.game.state == State.PLAYING:
                if key in {"escape", "p"}:
                    self.pause_selection = 0
                    self.confirm_leave = False
                    self.game.pause()
                elif key in DIRECTION_KEYS:
                    self.game.set_direction(DIRECTION_KEYS[key])
                else:
                    self.game.cheat(key)
                    if self.game.state in {State.GAME_OVER, State.VICTORY}:
                        self._ignore_finish_text = True
                        self._finish_trigger_key = key

    def _main_key(self, key: str) -> None:
        """Navigate all four required main-menu actions with a keyboard."""
        if key in {"up", "w"}:
            self.selection = (self.selection - 1) % 4
        elif key in {"down", "s"}:
            self.selection = (self.selection + 1) % 4
        elif key in {"enter", "space"}:
            if self.selection == 0:
                self.start()
            elif self.selection == 1:
                self.page = "highscores"
            elif self.selection == 2:
                self.page = "instructions"
            else:
                self.running = False
        elif key == "escape":
            self.running = False

    def _pause_key(self, key: str) -> None:
        """Require an explicit second confirmation before discarding a run."""
        if key in {"escape", "p"}:
            if self.confirm_leave:
                self.confirm_leave = False
            else:
                self.game.pause()
        elif key in {"up", "down", "w", "s"}:
            self.confirm_leave = False
            self.pause_selection = 1 - self.pause_selection
        elif key in {"enter", "space"}:
            if self.pause_selection == 0:
                self.game.pause()
            elif not self.confirm_leave:
                self.confirm_leave = True
            else:
                self.game.return_to_menu()
                self.page = "main"
                self.confirm_leave = False

    def _name_event(self, event: InputEvent) -> None:
        """Accept printable ASCII names with visible validation feedback."""
        if event.kind == "text":
            for char in event.text:
                if not (char.isascii() and (char.isalnum() or char == " ")):
                    self.message = "Use letters, numbers and spaces only."
                elif len(self.name) >= 10:
                    self.message = "Names have at most 10 characters."
                else:
                    self.name += char
                    self.message = ""
        elif event.kind == "key":
            if event.key == "backspace":
                self.name = self.name[:-1]
                self.message = ""
            elif event.key == "enter":
                if not self.name.strip():
                    self.message = "Enter a name, or Esc to save as PLAYER."
                else:
                    self._save_score(self.name.strip())
            elif event.key == "escape":
                self._save_score("PLAYER")

    def _save_score(self, name: str) -> None:
        """Record once, retain memory on write failure, and return to menu."""
        if not self.scores.add(name, self.game.score):
            self.message = "Use 1-10 letters, numbers or spaces."
            return
        self.scores.save()
        self.warning = self.scores.last_warning
        self.game.return_to_menu()
        self.page = "main"
        self.name = ""
        self.message = ""

    def draw(self) -> None:
        """Render the selected screen, keeping drawing free of game rules."""
        self.graphics.begin()
        log_warning = (
            "Error log unavailable; details printed to console."
            if self.log_session is not None and self.log_session.warning
            else ""
        )
        if self.page == "main":
            self.renderer.menu(self.scores.entries, self.selection)
            if log_warning:
                self.graphics.text(
                    log_warning, self.graphics.width // 2,
                    self.graphics.height - (50 if self.warning else 28),
                    size=18, color=(255, 181, 101), center=True,
                )
            if self.warning:
                self.graphics.text(
                    "Score file warning; leaderboard retained in memory.",
                    self.graphics.width // 2, self.graphics.height - 28,
                    size=18, color=(255, 181, 101), center=True,
                )
        elif self.page == "instructions":
            self.renderer.instructions()
        elif self.page == "highscores":
            self.renderer.highscores(self.scores.entries)
        elif self.page == "error":
            self.renderer.error(self.error_message)
        elif self.game.state == State.PAUSED:
            self.renderer.pause(self.game, self.pause_selection,
                                self.confirm_leave)
        elif self.game.state in {State.GAME_OVER, State.VICTORY}:
            self.renderer.finish(self.game, self.name,
                                 self.message or log_warning)
        else:
            self.renderer.game(self.game)
        self.graphics.present()
