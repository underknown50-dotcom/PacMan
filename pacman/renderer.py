"""Graphical rendering engine for Pac-Man using pygame-ce.

Complies strictly with Chapter 4 'MLX-equivalent' primitives:
- Uses only basic surface clears, line drawing, circle drawing, rect drawing,
  and pixel blitting.
- Implements all Chapter 6.8 screens:
  * Main Menu
  * In-Game HUD (Score, Lives, Level, Timer, Cheats)
  * Pause Menu
  * Game Over Screen
  * Victory Screen
  * Highscores Top 10 View
  * Instructions Screen
"""

import math
import pygame
from typing import List, Tuple
from pacman.adapter import MazeAdapter
from pacman.game import Game, GameState
from pacman.models import Direction, Ghost, GhostState


class Renderer:
    """Manages window surface, arcade drawing, and user interface screens."""

    TILE_SIZE = 28
    HUD_HEIGHT = 60
    COLOR_BG = (0, 0, 0)
    COLOR_WALL = (33, 33, 222)
    COLOR_SOLID = (20, 20, 100)
    COLOR_PACGUM = (255, 183, 174)
    COLOR_SUPER = (255, 255, 255)
    COLOR_PACMAN = (255, 255, 0)
    COLOR_HUD = (255, 255, 255)

    def __init__(self, game: Game) -> None:
        """Initialize display surface and typography fonts."""
        self.game = game
        self._init_window()

        self.font_title = pygame.font.Font(None, 46)
        self.font_header = pygame.font.Font(None, 34)
        self.font_normal = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)

        # Menu selections
        self.menu_options = [
            "Start Game",
            "View Highscores",
            "Instructions",
            "Exit",
        ]
        self.menu_cursor = 0

        self.pause_options = [
            "Resume Game",
            "Main Menu",
        ]
        self.pause_cursor = 0

        self.anim_timer = 0.0

    def _init_window(self) -> None:
        """Set up or resize the window according to maze dimensions."""
        width = max(640, self.game.maze.width * self.TILE_SIZE)
        maze_h = self.game.maze.height * self.TILE_SIZE
        height = max(520, maze_h + self.HUD_HEIGHT)
        self.screen_width = width
        self.screen_height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("42 Pac-Man")

    def resize_if_needed(self) -> None:
        """Resize display surface if level dimensions changed."""
        needed_w = max(640, self.game.maze.width * self.TILE_SIZE)
        needed_h = max(
            520, self.game.maze.height * self.TILE_SIZE + self.HUD_HEIGHT
        )
        if (
            needed_w != self.screen_width
            or needed_h != self.screen_height
        ):
            self._init_window()

    def render(self, dt: float) -> None:
        """Render the complete frame based on current game state."""
        self.anim_timer += dt
        self.resize_if_needed()
        self.screen.fill(self.COLOR_BG)

        if self.game.state == GameState.MENU:
            self._draw_main_menu()
        elif self.game.state == GameState.PLAYING:
            self._draw_gameplay()
        elif self.game.state == GameState.PAUSED:
            self._draw_gameplay()
            self._draw_pause_overlay()
        elif self.game.state == GameState.GAME_OVER:
            self._draw_gameplay()
            self._draw_game_over_screen()
        elif self.game.state == GameState.VICTORY:
            self._draw_gameplay()
            self._draw_victory_screen()
        elif self.game.state == GameState.HIGHSCORES:
            self._draw_highscores_screen()
        elif self.game.state == GameState.INSTRUCTIONS:
            self._draw_instructions_screen()

        pygame.display.flip()

    # ------------------ In-Game Rendering ------------------

    def _draw_gameplay(self) -> None:
        """Draw maze, pacgums, player, ghosts, and top HUD."""
        offset_x = (
            self.screen_width - (self.game.maze.width * self.TILE_SIZE)
        ) // 2
        available_h = self.screen_height - self.HUD_HEIGHT
        offset_y = self.HUD_HEIGHT + (
            available_h - (self.game.maze.height * self.TILE_SIZE)
        ) // 2

        self._draw_maze(offset_x, offset_y)
        self._draw_collectibles(offset_x, offset_y)
        self._draw_player(offset_x, offset_y)
        self._draw_ghosts(offset_x, offset_y)
        self._draw_hud()

    def _draw_maze(self, off_x: int, off_y: int) -> None:
        """Draw corridor walls and solid 42 center logo blocks."""
        ts = self.TILE_SIZE
        grid = self.game.maze.grid

        for y in range(self.game.maze.height):
            for x in range(self.game.maze.width):
                px = off_x + (x * ts)
                py = off_y + (y * ts)
                cell = grid[y][x]

                if cell == MazeAdapter.SOLID_BLOCK:
                    # Draw solid center logo block
                    pygame.draw.rect(
                        self.screen,
                        self.COLOR_SOLID,
                        (px + 1, py + 1, ts - 2, ts - 2),
                    )
                    pygame.draw.rect(
                        self.screen,
                        self.COLOR_WALL,
                        (px, py, ts, ts),
                        width=1,
                    )
                    continue

                # Wall lines (thickness 3)
                if cell & MazeAdapter.WALL_NORTH:
                    pygame.draw.line(
                        self.screen,
                        self.COLOR_WALL,
                        (px, py),
                        (px + ts, py),
                        width=3,
                    )
                if cell & MazeAdapter.WALL_EAST:
                    pygame.draw.line(
                        self.screen,
                        self.COLOR_WALL,
                        (px + ts, py),
                        (px + ts, py + ts),
                        width=3,
                    )
                if cell & MazeAdapter.WALL_SOUTH:
                    pygame.draw.line(
                        self.screen,
                        self.COLOR_WALL,
                        (px, py + ts),
                        (px + ts, py + ts),
                        width=3,
                    )
                if cell & MazeAdapter.WALL_WEST:
                    pygame.draw.line(
                        self.screen,
                        self.COLOR_WALL,
                        (px, py),
                        (px, py + ts),
                        width=3,
                    )

    def _draw_collectibles(self, off_x: int, off_y: int) -> None:
        """Render small pacgums and pulsating super-pacgums."""
        ts = self.TILE_SIZE

        # Regular pacgums
        for gx, gy in self.game.pacgums:
            cx = off_x + int((gx + 0.5) * ts)
            cy = off_y + int((gy + 0.5) * ts)
            pygame.draw.circle(
                self.screen, self.COLOR_PACGUM, (cx, cy), radius=3
            )

        # Super-pacgums (pulsating animation)
        pulse = 6 + int(math.sin(self.anim_timer * 8.0) * 2)
        for sx, sy in self.game.super_pacgums:
            cx = off_x + int((sx + 0.5) * ts)
            cy = off_y + int((sy + 0.5) * ts)
            pygame.draw.circle(
                self.screen, self.COLOR_SUPER, (cx, cy), radius=pulse
            )

    def _draw_player(self, off_x: int, off_y: int) -> None:
        """Draw animated Pac-Man with mouth facing movement direction."""
        ts = self.TILE_SIZE
        px = off_x + int((self.game.player.x + 0.5) * ts)
        py = off_y + int((self.game.player.y + 0.5) * ts)
        radius = ts // 2 - 2

        # Mouth wedge angle calculation
        mouth_anim = abs(math.sin(self.anim_timer * 12.0)) * 0.7 + 0.1
        facing = self.game.player.direction
        base_angle = 0.0

        if facing == Direction.RIGHT or facing == Direction.NONE:
            base_angle = 0.0
        elif facing == Direction.DOWN:
            base_angle = math.pi * 0.5
        elif facing == Direction.LEFT:
            base_angle = math.pi
        elif facing == Direction.UP:
            base_angle = math.pi * 1.5

        start_angle = base_angle + (mouth_anim * 0.5)
        end_angle = base_angle + (2 * math.pi) - (mouth_anim * 0.5)

        points: List[Tuple[int, int]] = [(px, py)]
        steps = 16
        for s in range(steps + 1):
            theta = start_angle + (end_angle - start_angle) * (s / steps)
            dx = int(math.cos(theta) * radius)
            dy = int(math.sin(theta) * radius)
            points.append((px + dx, py + dy))

        if len(points) >= 3:
            pygame.draw.polygon(self.screen, self.COLOR_PACMAN, points)
        else:
            pygame.draw.circle(
                self.screen, self.COLOR_PACMAN, (px, py), radius
            )

    def _draw_ghosts(self, off_x: int, off_y: int) -> None:
        """Draw 4 ghosts with classic arcade silhouettes, eyes, and states."""
        ts = self.TILE_SIZE

        for ghost in self.game.ghosts:
            gx = off_x + int(ghost.x * ts)
            gy = off_y + int(ghost.y * ts)
            w = ts - 2
            h = ts - 2

            # Color selection based on state
            if ghost.state == GhostState.EATEN:
                # Only draw eyes returning home
                self._draw_ghost_eyes(gx, gy, w, h, ghost.direction)
                continue

            if ghost.state == GhostState.FRIGHTENED:
                # Flashes blue/white when expiring
                if (
                    ghost.frightened_timer < 2.5
                    and int(self.anim_timer * 6.0) % 2 == 0
                ):
                    body_color = (255, 255, 255)
                else:
                    body_color = (36, 36, 255)
            else:
                body_color = Ghost.COLORS[ghost.ghost_type]

            # Ghost dome top
            rect_top = pygame.Rect(gx, gy, w, h // 2)
            pygame.draw.rect(
                self.screen,
                body_color,
                rect_top,
                border_top_left_radius=w // 2,
                border_top_right_radius=w // 2,
            )

            # Ghost skirt body
            rect_bot = pygame.Rect(gx, gy + (h // 4), w, (h * 3) // 4)
            pygame.draw.rect(self.screen, body_color, rect_bot)

            # Wavy tentacles at bottom
            tentacle_w = w // 3
            for t in range(3):
                tx = gx + (t * tentacle_w)
                ty = gy + h - 3
                pygame.draw.circle(
                    self.screen,
                    body_color,
                    (tx + tentacle_w // 2, ty),
                    tentacle_w // 2,
                )

            # Eyes
            if ghost.state == GhostState.FRIGHTENED:
                # Frightened face (small dots)
                eye_y = gy + (h // 3)
                pygame.draw.circle(
                    self.screen, (255, 200, 200), (gx + 6, eye_y), 2
                )
                pygame.draw.circle(
                    self.screen, (255, 200, 200), (gx + w - 6, eye_y), 2
                )
            else:
                self._draw_ghost_eyes(gx, gy, w, h, ghost.direction)

    def _draw_ghost_eyes(
        self, gx: int, gy: int, w: int, h: int, direction: Direction
    ) -> None:
        """Draw expressive white ghost eyes with directional pupils."""
        pdx, pdy = direction.dx, direction.dy
        eye_y = gy + (h // 3)
        left_eye_x = gx + (w // 3) - 2
        right_eye_x = gx + ((2 * w) // 3) + 2

        # White eye bases
        pygame.draw.circle(
            self.screen, (255, 255, 255), (left_eye_x, eye_y), 4
        )
        pygame.draw.circle(
            self.screen, (255, 255, 255), (right_eye_x, eye_y), 4
        )

        # Pupils looking in movement direction
        pupil_color = (0, 0, 180)
        pygame.draw.circle(
            self.screen,
            pupil_color,
            (left_eye_x + pdx * 2, eye_y + pdy * 2),
            2,
        )
        pygame.draw.circle(
            self.screen,
            pupil_color,
            (right_eye_x + pdx * 2, eye_y + pdy * 2),
            2,
        )

    def _draw_hud(self) -> None:
        """Render in-game HUD with score, lives, level, time, and cheats."""
        hud_surface = pygame.Surface((self.screen_width, self.HUD_HEIGHT))
        hud_surface.fill((10, 10, 10))

        score_text = self.font_header.render(
            f"SCORE: {self.game.score}", True, (255, 255, 0)
        )
        hud_surface.blit(score_text, (15, 8))

        lvl_text = self.font_normal.render(
            f"LEVEL: {self.game.current_level_idx + 1}",
            True,
            (255, 255, 255),
        )
        hud_surface.blit(lvl_text, (220, 12))

        time_val = max(0, int(self.game.level_time_remaining))
        time_color = (255, 60, 60) if time_val < 15 else (255, 255, 255)
        time_text = self.font_normal.render(
            f"TIME: {time_val}s", True, time_color
        )
        hud_surface.blit(time_text, (330, 12))

        # Lives icons
        lives_label = self.font_normal.render("LIVES:", True, (255, 255, 255))
        hud_surface.blit(lives_label, (440, 12))
        for i in range(min(5, self.game.player.lives)):
            pygame.draw.circle(
                hud_surface,
                self.COLOR_PACMAN,
                (510 + (i * 18), 20),
                radius=7,
            )
        if self.game.player.lives > 5:
            extra_txt = self.font_small.render(
                f"+{self.game.player.lives - 5}", True, (255, 255, 0)
            )
            hud_surface.blit(extra_txt, (605, 12))

        # Active cheat badges
        if self.game.active_cheats:
            badge_str = "CHEATS: " + ", ".join(
                sorted(self.game.active_cheats)
            )
            cheat_txt = self.font_small.render(
                badge_str, True, (0, 255, 120)
            )
            hud_surface.blit(cheat_txt, (15, 38))

        self.screen.blit(hud_surface, (0, 0))
        pygame.draw.line(
            self.screen,
            (60, 60, 180),
            (0, self.HUD_HEIGHT - 1),
            (self.screen_width, self.HUD_HEIGHT - 1),
            width=2,
        )

    # ------------------ Menus & State Screens ------------------

    def _draw_main_menu(self) -> None:
        """Render the primary Main Menu screen."""
        title = self.font_title.render("PAC-MAN", True, (255, 255, 0))
        sub = self.font_normal.render(
            "42 EDITION", True, (0, 200, 255)
        )
        self.screen.blit(
            title, (self.screen_width // 2 - title.get_width() // 2, 70)
        )
        self.screen.blit(
            sub, (self.screen_width // 2 - sub.get_width() // 2, 120)
        )

        start_y = 200
        for i, opt in enumerate(self.menu_options):
            is_sel = i == self.menu_cursor
            color = (255, 255, 0) if is_sel else (180, 180, 180)
            txt = self.font_header.render(opt, True, color)
            opt_x = self.screen_width // 2 - 80
            opt_y = start_y + (i * 45)
            self.screen.blit(txt, (opt_x, opt_y))

            if is_sel:
                arrow = [
                    (opt_x - 24, opt_y + 4),
                    (opt_x - 24, opt_y + 20),
                    (opt_x - 10, opt_y + 12),
                ]
                pygame.draw.polygon(self.screen, (255, 255, 0), arrow)

        footer = self.font_small.render(
            "Use UP/DOWN to navigate, ENTER to select",
            True,
            (120, 120, 120),
        )
        self.screen.blit(
            footer,
            (
                self.screen_width // 2 - footer.get_width() // 2,
                self.screen_height - 40,
            ),
        )

    def _draw_pause_overlay(self) -> None:
        """Render semi-transparent pause menu overlay."""
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("GAME PAUSED", True, (255, 255, 255))
        self.screen.blit(
            title, (self.screen_width // 2 - title.get_width() // 2, 140)
        )

        start_y = 240
        for i, opt in enumerate(self.pause_options):
            is_sel = i == self.pause_cursor
            color = (255, 255, 0) if is_sel else (180, 180, 180)
            txt = self.font_header.render(opt, True, color)
            opt_x = self.screen_width // 2 - 80
            opt_y = start_y + (i * 50)
            self.screen.blit(txt, (opt_x, opt_y))

            if is_sel:
                arrow = [
                    (opt_x - 24, opt_y + 4),
                    (opt_x - 24, opt_y + 20),
                    (opt_x - 10, opt_y + 12),
                ]
                pygame.draw.polygon(self.screen, (255, 255, 0), arrow)

    def _draw_game_over_screen(self) -> None:
        """Render Game Over screen with interactive highscore name prompt."""
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("GAME OVER", True, (255, 50, 50))
        score_txt = self.font_header.render(
            f"FINAL SCORE: {self.game.score}", True, (255, 255, 0)
        )
        self.screen.blit(
            title, (self.screen_width // 2 - title.get_width() // 2, 110)
        )
        self.screen.blit(
            score_txt,
            (self.screen_width // 2 - score_txt.get_width() // 2, 170),
        )

        self._draw_name_input_box(240)

    def _draw_victory_screen(self) -> None:
        """Render Victory screen with celebratory congratulatory message."""
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("VICTORY!", True, (0, 255, 120))
        sub = self.font_normal.render(
            "CONGRATULATIONS! ALL 10 LEVELS CONQUERED!",
            True,
            (255, 255, 255),
        )
        score_txt = self.font_header.render(
            f"FINAL SCORE: {self.game.score}", True, (255, 255, 0)
        )

        self.screen.blit(
            title, (self.screen_width // 2 - title.get_width() // 2, 90)
        )
        self.screen.blit(
            sub, (self.screen_width // 2 - sub.get_width() // 2, 140)
        )
        self.screen.blit(
            score_txt,
            (self.screen_width // 2 - score_txt.get_width() // 2, 180),
        )

        self._draw_name_input_box(250)

    def _draw_name_input_box(self, y_pos: int) -> None:
        """Draw the highscore name entry text box."""
        prompt = self.font_normal.render(
            "Enter your name (max 10 alphanumeric characters):",
            True,
            (200, 200, 200),
        )
        self.screen.blit(
            prompt, (self.screen_width // 2 - prompt.get_width() // 2, y_pos)
        )

        box_w, box_h = 240, 40
        box_x = self.screen_width // 2 - (box_w // 2)
        box_y = y_pos + 35

        pygame.draw.rect(
            self.screen, (30, 30, 30), (box_x, box_y, box_w, box_h)
        )
        pygame.draw.rect(
            self.screen, (255, 255, 0), (box_x, box_y, box_w, box_h), width=2
        )

        cursor = "_" if int(self.anim_timer * 4.0) % 2 == 0 else ""
        name_display = (self.game.name_input + cursor) or cursor
        name_txt = self.font_header.render(
            name_display, True, (255, 255, 255)
        )
        self.screen.blit(
            name_txt,
            (box_x + 12, box_y + (box_h // 2 - name_txt.get_height() // 2)),
        )

        tip = self.font_small.render(
            "Press ENTER to save and return to menu",
            True,
            (140, 140, 140),
        )
        self.screen.blit(
            tip, (self.screen_width // 2 - tip.get_width() // 2, box_y + 55)
        )

    def _draw_highscores_screen(self) -> None:
        """Display the persistent Top 10 highscores table."""
        title = self.font_title.render(
            "TOP 10 HIGHSCORES", True, (255, 255, 0)
        )
        self.screen.blit(
            title, (self.screen_width // 2 - title.get_width() // 2, 40)
        )

        scores = self.game.highscores.get_top_entries()
        start_y = 110

        if not scores:
            empty_txt = self.font_normal.render(
                "No scores recorded yet. Go play a game!",
                True,
                (180, 180, 180),
            )
            self.screen.blit(
                empty_txt,
                (self.screen_width // 2 - empty_txt.get_width() // 2, 200),
            )
        else:
            mid_x = self.screen_width // 2
            rank_x = mid_x - 140
            name_x = mid_x - 60
            score_x = mid_x + 140

            # Table column headers
            r_hdr = self.font_normal.render("RANK", True, (0, 200, 255))
            n_hdr = self.font_normal.render("NAME", True, (0, 200, 255))
            s_hdr = self.font_normal.render("SCORE", True, (0, 200, 255))
            self.screen.blit(r_hdr, (rank_x, start_y))
            self.screen.blit(n_hdr, (name_x, start_y))
            self.screen.blit(s_hdr, (score_x - s_hdr.get_width(), start_y))

            pygame.draw.line(
                self.screen,
                (40, 40, 100),
                (rank_x, start_y + 24),
                (score_x, start_y + 24),
                width=1,
            )

            for rank, (name, sc) in enumerate(scores, start=1):
                color = (
                    (255, 215, 0)
                    if rank == 1
                    else (210, 210, 210)
                )
                row_y = start_y + 10 + (rank * 26)
                r_txt = self.font_normal.render(str(rank), True, color)
                n_txt = self.font_normal.render(name, True, color)
                s_txt = self.font_normal.render(f"{sc:,}", True, color)

                self.screen.blit(r_txt, (rank_x + 8, row_y))
                self.screen.blit(n_txt, (name_x, row_y))
                self.screen.blit(s_txt, (score_x - s_txt.get_width(), row_y))

        footer = self.font_small.render(
            "Press ESC or ENTER to return to Main Menu",
            True,
            (140, 140, 140),
        )
        self.screen.blit(
            footer,
            (
                self.screen_width // 2 - footer.get_width() // 2,
                self.screen_height - 35,
            ),
        )

    def _draw_instructions_screen(self) -> None:
        """Display controls, game rules, and peer review cheat guide."""
        title = self.font_title.render("INSTRUCTIONS", True, (255, 255, 0))
        self.screen.blit(
            title, (self.screen_width // 2 - title.get_width() // 2, 35)
        )

        cyan = (0, 200, 255)
        white = (220, 220, 220)
        orange = (255, 180, 0)
        gray = (200, 200, 200)

        lines = [
            ("CONTROLS:", cyan),
            ("  * Arrow Keys / WASD : Steer Pac-Man through corridors", white),
            ("  * P                 : Pause / Resume ongoing game", white),
            ("  * ESC               : Return to Main Menu", white),
            ("", (0, 0, 0)),
            ("GAMEPLAY RULES:", cyan),
            ("  * Eat all small pacgums in corridors to clear level", white),
            ("  * Super-pacgums in 4 corners turn ghosts edible!", white),
            ("  * 4 ghost personalities: Blinky, Pinky, Inky & Clyde", white),
            ("  * Complete all 10 campaign levels to achieve VICTORY", white),
            ("", (0, 0, 0)),
            ("CHEAT HOTKEYS (Chapter 6.5 Review Mode):", orange),
            ("  * [ I ] : Toggle Invincibility (never lose lives)", gray),
            ("  * [ L ] : Level Skip (instantly complete level)", gray),
            ("  * [ F ] : Freeze Ghosts (halt all ghost movement)", gray),
            ("  * [ + ] : Extra Life (add 1 remaining life)", gray),
            ("  * [ B ] : Speed Boost (move +60% faster)", gray),
        ]

        start_y = 90
        for text, color in lines:
            if text:
                txt = self.font_small.render(text, True, color)
                self.screen.blit(txt, (40, start_y))
            start_y += 20

        footer = self.font_small.render(
            "Press ESC or ENTER to return to Main Menu",
            True,
            (140, 140, 140),
        )
        self.screen.blit(
            footer,
            (
                self.screen_width // 2 - footer.get_width() // 2,
                self.screen_height - 35,
            ),
        )
