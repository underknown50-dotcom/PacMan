"""Draw the arcade interface using only the restricted graphics facade."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from .finish_background import FinishBackground
from .graphics import Color, Graphics
from .highscores import ScoreEntry
from .menu_background import GardenBackground

if TYPE_CHECKING:
    from .models import Game


INK: Color = (231, 237, 251)
MUTED: Color = (140, 156, 187)
YELLOW: Color = (255, 214, 66)
CYAN: Color = (69, 216, 245)
PANEL: Color = (17, 24, 42)
EDGE: Color = (39, 55, 86)
WALL: Color = (53, 118, 234)
RED: Color = (255, 112, 131)
GHOST_COLORS: tuple[Color, ...] = (
    (255, 102, 124),
    (253, 162, 214),
    (64, 219, 226),
    (255, 178, 91),
)


class Renderer:
    """Present each application state with a consistent keyboard-first UI."""

    def __init__(self, graphics: Graphics) -> None:
        """Keep the platform-independent drawing interface."""
        self.g = graphics
        self._garden = GardenBackground(graphics)
        self._finish_background = FinishBackground(graphics)

    def _chrome(
        self, title: str, subtitle: str = "42 / ARCADE", clear: bool = True,
    ) -> None:
        """Clear the screen and draw the common thin masthead."""
        if clear:
            self.g.begin()
        self.g.rect(35, 31, 9, 9, YELLOW)
        self.g.text(title, 54, 25, 24, INK)
        self.g.text(subtitle, 792, 28, 19, MUTED)
        self.g.rect(35, 63, self.g.width - 70, 1, EDGE)
        for x, y in ((74, 111), (937, 163), (911, 718), (49, 721)):
            self.g.rect(x, y, 2, 2, EDGE)

    def _panel(self, x: int, y: int, w: int, h: int) -> None:
        """Draw a restrained rectangular panel with a subtle border."""
        self.g.rect(x, y, w, h, EDGE)
        self.g.rect(x + 1, y + 1, w - 2, h - 2, PANEL)

    def _footer(self, text: str) -> None:
        """Place consistent navigation guidance below the screen content."""
        self.g.rect(35, 775, self.g.width - 70, 1, EDGE)
        self.g.text(text, self.g.width // 2, 797, 21, MUTED, True)

    def _choices(
        self,
        choices: tuple[str, ...],
        selection: int,
        x: int,
        y: int,
        width: int,
        step: int = 58,
    ) -> None:
        """Render selectable menu rows with a visible keyboard focus."""
        for index, label in enumerate(choices):
            top = y + index * step
            selected = index == selection
            if selected:
                self.g.rect(x, top, width, step - 8, (46, 43, 35))
                self.g.rect(x, top, 3, step - 8, YELLOW)
                self.g.player(x + 24, top + 24, 9, phase=2)
            self.g.text(
                label, x + 46, top + 12, 29, YELLOW if selected else MUTED
            )
            self.g.text(
                f"0{index + 1}", x + width - 35, top + 16, 19, MUTED
            )

    def menu(self, entries: list[ScoreEntry], selection: int) -> None:
        """Layer readable navigation over a gently moving twilight garden."""
        self._garden.draw()
        self._chrome("PAC-MAN 42", "THE GARDEN / AFTER HOURS", clear=False)
        self.g.text("A NEW PATH. A FRESH START.", 58, 101, 19,
                    (153, 187, 170))
        self.g.text("MAZE", 54, 136, 91, INK)
        self.g.text("CHASE.", 54, 215, 91, YELLOW)
        self.g.text("A little calm before the chase.", 58, 307, 25,
                    (183, 207, 192))
        now = time.monotonic()
        self.g.player(700, 374, 23, phase=int(now * 8) % 4)
        for index, color in enumerate(GHOST_COLORS):
            y = round(374 + math.sin(now * 1.4 + index * .8) * 3)
            self.g.ghost(762 + index * 42, y, 14, color,
                         phase=int(now * 3) % 2)
        self._garden_card(54, 361, 425, 323)
        self.g.text("YOUR NEXT ADVENTURE", 78, 383, 18, (151, 181, 164))
        self._garden_choices(selection)
        self._garden_card(606, 434, 340, 250)
        self.g.text("TOP SCORES", 630, 458, 22, (168, 216, 189))
        self.g.text("TOP 5", 880, 461, 16, (147, 176, 160))
        self.g.rect(630, 491, 292, 1, (44, 77, 65))
        if not entries:
            self.g.text("A fresh leaderboard.", 631, 532, 25, INK)
            self.g.text("Leave your first mark.", 631, 568, 22,
                        (151, 181, 164))
        for index, entry in enumerate(entries[:5]):
            top = 510 + index * 31
            color = YELLOW if index == 0 else INK
            self.g.text(f"{index + 1:02}", 631, top, 20,
                        (140, 171, 153))
            self.g.text(entry.name, 667, top, 22, color)
            score_size = min(22, max(13, 155 // len(str(entry.score))))
            self.g.text(str(entry.score), 838, top, score_size, color)
        self._rounded(291, 734, 418, 31, 15, (16, 43, 38))
        self.g.text("FRESH MAZES  /  FOUR GHOSTS  /  ONE MORE RUN",
                    500, 744, 17, (181, 207, 185), True)
        self._rounded(54, 786, 892, 37, 15, (10, 29, 30))
        self.g.text("UP / DOWN  Select       ENTER  Play       ESC  Exit",
                    500, 797, 20, (192, 214, 201), True)
        self.g.present()

    def _rounded(
        self, x: int, y: int, w: int, h: int, radius: int, color: Color,
    ) -> None:
        """Build a rounded card from pixel-buffer rectangles and circles."""
        self.g.rect(x + radius, y, w - radius * 2, h, color)
        self.g.rect(x, y + radius, w, h - radius * 2, color)
        for cx in (x + radius, x + w - radius - 1):
            for cy in (y + radius, y + h - radius - 1):
                self.g.circle(cx, cy, radius, color)

    def _garden_card(self, x: int, y: int, w: int, h: int) -> None:
        """Keep menu text legible on quiet, softly edged garden panels."""
        self._rounded(x, y + 6, w, h, 17, (12, 34, 30))
        self._rounded(x, y, w, h, 17, (56, 86, 72))
        self._rounded(x + 1, y + 1, w - 2, h - 2, 16, (14, 36, 33))
        self.g.line(x + 24, y + 1, x + w - 25, y + 1, (84, 111, 88))

    def _garden_choices(self, selection: int) -> None:
        """Highlight keyboard focus with a warm card, marker and chevron."""
        labels = ("Start Game", "View Highscores", "Instructions", "Exit")
        for index, label in enumerate(labels):
            y = 422 + index * 59
            selected = index == selection
            if selected:
                self._rounded(71, y - 6, 391, 50, 10, (48, 68, 46))
                self.g.rect(72, y + 5, 3, 28, YELLOW)
                self.g.player(94, y + 19, 9, phase=2)
            else:
                self.g.text(f"0{index + 1}", 87, y + 10, 18,
                            (115, 153, 131))
            self.g.text(label, 121, y + 5, 29,
                        YELLOW if selected else (186, 207, 194))
            if selected:
                self.g.line(433, y + 14, 439, y + 20, YELLOW, 2)
                self.g.line(439, y + 20, 433, y + 26, YELLOW, 2)

    def highscores(self, entries: list[ScoreEntry]) -> None:
        """Show the persistent ranked top ten and an empty-state message."""
        self._chrome("HIGH SCORES")
        self.g.text("THE HALL OF CHASE", 500, 106, 53, YELLOW, True)
        self.g.text("Your best ten runs. Every point counts.",
                    500, 170, 23, MUTED, True)
        self._panel(155, 221, 690, 504)
        self.g.text("RANK", 183, 244, 18, MUTED)
        self.g.text("PLAYER", 297, 244, 18, MUTED)
        self.g.text("SCORE", 690, 244, 18, MUTED)
        self.g.rect(181, 276, 638, 1, EDGE)
        if not entries:
            self.g.player(500, 427, 29)
            self.g.text("No saved runs yet.", 500, 495, 31, INK, True)
            self.g.text("Start a game and make your mark.",
                        500, 537, 23, MUTED, True)
        for index, entry in enumerate(entries[:10]):
            top = 296 + index * 40
            color = YELLOW if index == 0 else INK
            self.g.text(f"{index + 1:02}", 195, top, 26, MUTED)
            self.g.text(entry.name, 297, top, 28, color)
            self.g.text(str(entry.score), 690, top, 28, color)
        self._footer("ENTER / ESC  Return to Main Menu")
        self.g.present()

    def instructions(self) -> None:
        """Explain movement, scoring, persistence and every review control."""
        self._chrome("HOW TO PLAY")
        self.g.text("KNOW THE MAZE.", 46, 104, 52, YELLOW)
        self.g.text("Eat every pellet. Outsmart four ghosts. Clear each maze.",
                    49, 161, 24, MUTED)
        self._panel(45, 214, 440, 355)
        self._panel(506, 214, 449, 492)
        self.g.text("THE CONTROLS", 67, 237, 24, CYAN)
        left = (
            ("ARROWS / WASD", "Move & queue a turn"),
            ("ESC / P", "Pause / resume"),
            ("UP / DOWN", "Select menu item"),
            ("ENTER", "Confirm / save score"),
            ("F1", "Toggle review mode"),
        )
        for index, (key, description) in enumerate(left):
            top = 285 + index * 48
            self.g.text(key, 68, top, 20, YELLOW)
            self.g.text(description, 228, top, 21, INK)
        self.g.text("REVIEW MODE", 529, 237, 24, CYAN)
        self.g.text("Enable F1 first; active flags appear in the HUD.",
                    529, 274, 19, MUTED)
        right = (
            ("I", "Invincibility on / off"),
            ("N", "Complete level / final victory"),
            ("G", "Freeze / unfreeze ghosts"),
            ("L", "Add one life"),
            ("B", "Ten-second speed boost"),
            ("O", "Activate power-up"),
            ("C", "Leave one collectible"),
            ("T", "Set timer to one second"),
            ("K", "Lose one life"),
        )
        for index, (key, description) in enumerate(right):
            top = 313 + index * 39
            self.g.text(key, 535, top, 24, YELLOW)
            self.g.text(description, 578, top, 22, INK)
        self.g.text("THE RULES", 67, 595, 23, CYAN)
        rules = (
            "Large corner pellets make ghosts edible.",
            "Blue ghosts flee; flashing warns power is ending.",
            "Eaten ghosts return home as harmless eyes.",
            "Eat every pellet. Contact costs a life; timeout ends the run.",
        )
        for index, line in enumerate(rules):
            self.g.text(line, 47, 629 + index * 26, 20, INK)
        self.g.text("Names: 1-10 ASCII letters/digits/spaces; ESC = PLAYER.",
                    500, 744, 21, MUTED, True)
        self._footer("ENTER / ESC  Return to Main Menu")
        self.g.present()

    def _hud(self, game: Game) -> None:
        """Show the score, lives, progression and timer above the board."""
        self._chrome("PAC-MAN 42", "EAT. CHASE. REPEAT.")
        values = (
            ("SCORE", str(game.score), YELLOW),
            ("LIVES", str(game.lives), INK),
            ("LEVEL", f"{game.level_index + 1}/{len(game.config.levels)}",
             INK),
            ("TIME", f"{math.ceil(max(0, game.time_left)):03}s",
             RED if game.time_left < 15 else CYAN),
            ("PELLETS", str(len(game.pellets) + len(game.powers)), INK),
        )
        for index, (label, value, color) in enumerate(values):
            x = 35 + index * 188
            self._panel(x, 79, 178, 69)
            self.g.text(label, x + 13, 88, 16, MUTED)
            self.g.text(value, x + 13, 109, 32, color)

    def _board(self, game: Game) -> None:
        """Rasterize the original wall masks and moving actors accurately."""
        maze = game.maze
        tile = min(890 // maze.width, 594 // maze.height)
        board_width = maze.width * tile
        board_height = maze.height * tile
        left = (self.g.width - board_width) // 2
        top = 163 + (594 - board_height) // 2
        self.g.rect(left - 7, top - 7, board_width + 14,
                    board_height + 14, (17, 27, 48))
        self.g.rect(left, top, board_width, board_height, (9, 16, 31))
        wall_width = max(1, tile // 11)
        for row, masks in enumerate(maze.walls):
            for col, mask in enumerate(masks):
                x, y = left + col * tile, top + row * tile
                if mask == 15:
                    self.g.rect(x + 2, y + 2, tile - 3, tile - 3,
                                (28, 56, 102))
                if mask & 1:
                    self.g.rect(x, y, tile + wall_width, wall_width, WALL)
                if mask & 8:
                    self.g.rect(x, y, wall_width, tile + wall_width, WALL)
                if row == maze.height - 1 and mask & 4:
                    self.g.rect(x, y + tile, tile + wall_width,
                                wall_width, WALL)
                if col == maze.width - 1 and mask & 2:
                    self.g.rect(x + tile, y, wall_width,
                                tile + wall_width, WALL)
        for x, y in game.pellets:
            self.g.circle(left + x * tile + tile // 2,
                          top + y * tile + tile // 2,
                          max(1, tile // 12), (245, 218, 173))
        now = time.monotonic()
        pulse = int(now * 4) % 2
        for x, y in game.powers:
            self.g.circle(left + x * tile + tile // 2,
                          top + y * tile + tile // 2,
                          max(3, tile // 5) - pulse, YELLOW)
        radius = max(4, int(tile * 0.35))
        for index, ghost in enumerate(game.ghosts):
            px, py = ghost.position()
            direction = ghost.direction.name if ghost.direction else "LEFT"
            if not ghost.active:
                self.g.eyes(
                    left + round((px + 0.5) * tile),
                    top + round((py + 0.5) * tile), radius, direction,
                )
                continue
            color = GHOST_COLORS[index % 4]
            frightened = game.power_left > 0
            if frightened:
                color = (49, 95, 232)
                if game.power_left < 2 and pulse:
                    color = (140, 173, 244)
            self.g.ghost(
                left + round((px + 0.5) * tile),
                top + round((py + 0.5) * tile), radius, color,
                direction, frightened, pulse,
            )
        if game.invulnerable_left <= 0 or int(now * 9) % 2 == 0:
            px, py = game.player.position()
            direction = (game.player.direction.name
                         if game.player.direction else "RIGHT")
            self.g.player(
                left + round((px + 0.5) * tile),
                top + round((py + 0.5) * tile), radius,
                direction, int(now * 11) % 4,
            )

    def _game_footer(self, game: Game) -> None:
        """Expose active power, review state and concise playing controls."""
        if game.cheats.enabled:
            flags = ["REVIEW ON"]
            if game.cheats.invincible:
                flags.append("INVINCIBLE")
            if game.cheats.frozen:
                flags.append("GHOSTS FROZEN")
            if game.boost_left > 0:
                flags.append(f"BOOST {game.boost_left:.0f}s")
            self.g.text(" / ".join(flags), 500, 770, 20, YELLOW, True)
            self.g.text("I God  N Next  G Freeze  L Life  B Boost  O Power  "
                        "C Last  T Timeout  K Hurt  F1 Off",
                        500, 806, 19, MUTED, True)
        else:
            label = "ARROWS / WASD Move    ESC / P Pause    F1 Review mode"
            if game.power_left > 0:
                self.g.text(f"GHOSTS EDIBLE  {game.power_left:.1f}s",
                            500, 770, 22, CYAN, True)
            self.g.text(label, 500, 806, 21, MUTED, True)

    def game(self, game: Game) -> None:
        """Show gameplay and its noninteractive level transition overlay."""
        self._hud(game)
        self._board(game)
        self._game_footer(game)
        if game.state.value == "transition":
            self._panel(237, 330, 526, 168)
            self.g.text("MAZE CLEARED", 500, 362, 47, YELLOW, True)
            self.g.text("Fresh corridors. Same determination.",
                        500, 425, 26, INK, True)
        self.g.present()

    def pause(self, game: Game, selection: int, confirm: bool) -> None:
        """Display a pause menu and an explicit discard-run confirmation."""
        self._hud(game)
        self._board(game)
        self._panel(222, 282, 556, 305)
        self.g.text("PAUSED", 500, 308, 49, YELLOW, True)
        if confirm:
            self.g.text("Return to the menu and discard this run?",
                        500, 381, 25, INK, True)
            self.g.text("This score will not be saved.",
                        500, 420, 23, MUTED, True)
            self.g.text("ENTER  Discard run        ESC  Keep playing",
                        500, 508, 22, YELLOW, True)
        else:
            self.g.text("Take a breath. All gameplay timers are frozen.",
                        500, 368, 23, MUTED, True)
            self._choices(("Resume", "Return to Main Menu"),
                          selection, 266, 424, 468)
        self._footer("UP / DOWN Select       ENTER Confirm       ESC Resume")
        self.g.present()

    def finish(self, game: Game, name: str, message: str) -> None:
        """Present a distinct illustrated result and the existing save flow."""
        victory = game.state.value == "victory"
        self._finish_background.draw(victory)
        self._chrome("RUN COMPLETE" if victory else "END OF RUN",
                     "THE GARDEN / AFTER HOURS", clear=False)
        accent = YELLOW if victory else (174, 205, 250)
        muted = (165, 190, 166) if victory else (151, 174, 207)
        edge = (73, 96, 60) if victory else (58, 81, 116)
        panel = (14, 34, 29) if victory else (14, 25, 44)
        heading = "EVERY PATH CONQUERED" if victory else "THE CHASE RESTS"
        self.g.text(heading, 500, 102, 20, muted, True)
        title = "VICTORY!" if victory else "GAME OVER"
        self.g.text(title, 500, 133, 83, accent, True)
        total = len(game.config.levels)
        subtitle = f"All {total} mazes cleared. A run to remember."
        if not victory:
            subtitle = game.reason or "Your next run is waiting."
        self.g.text(subtitle[:78], 500, 223, 25, INK, True)
        self._finish_background.emblem(victory, 500, 290)
        self._rounded(203, 353, 594, 389, 19, (7, 20, 25))
        self._rounded(203, 347, 594, 389, 19, edge)
        self._rounded(204, 348, 592, 387, 18, panel)
        self.g.text("FINAL SCORE", 500, 369, 19, muted, True)
        score_size = min(59, max(29, 720 // max(1, len(str(game.score)))))
        self.g.text(str(game.score), 500, 397, score_size, accent, True)
        label = "MAZES CLEARED" if victory else "LEVEL REACHED"
        level = total if victory else min(total, game.level_index + 1)
        self.g.text(f"{label}  {level:02} / {total:02}",
                    383, 466, 21, INK, True)
        self.g.text(f"LIVES LEFT  {game.lives}", 657, 466, 21, INK, True)
        self.g.rect(235, 503, 530, 1, edge)
        self.g.text("SAVE YOUR RUN", 500, 525, 24, accent, True)
        self._rounded(284, 563, 432, 61, 10, edge)
        self._rounded(285, 564, 430, 59, 9, (8, 19, 31))
        cursor = "_" if int(time.monotonic() * 2) % 2 else " "
        self.g.text(name + cursor, 500, 580, 35, INK, True)
        self.g.text(f"{len(name)}/10   Letters, numbers and spaces only",
                    500, 642, 20, muted, True)
        if message:
            self.g.text(message[:64], 500, 685, 21, (255, 170, 158), True)
        else:
            prompt = "Your next adventure starts with your name."
            if not victory:
                prompt = "Save this run. The next path is waiting."
            self.g.text(prompt, 500, 685, 21, INK, True)
        self._rounded(120, 784, 760, 39, 15, (10, 23, 34))
        self.g.text("ENTER Save    BACKSPACE Delete    ESC Save as PLAYER",
                    500, 797, 21, INK, True)
        self.g.present()

    def error(self, message: str) -> None:
        """Show a readable runtime failure and a safe route to the menu."""
        self._chrome("UNABLE TO START")
        self.g.text("A SMALL DETOUR.", 500, 196, 58, RED, True)
        self._panel(130, 307, 740, 273)
        words = message.split()
        lines: list[str] = []
        line = ""
        for word in words:
            if len(line) + len(word) > 58:
                lines.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            lines.append(line)
        for index, item in enumerate(lines[:6]):
            self.g.text(item, 500, 345 + index * 32, 25, INK, True)
        self._footer("ENTER / ESC  Return to Main Menu")
        self.g.present()
