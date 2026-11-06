"""Small pygame facade restricted to operations with MLX equivalents.

The game uses a window, writable image buffers, image copies, strings, keyboard
hooks and a paced event loop. Shapes below are rasterized into those buffers;
there is no dependency on pygame's shape, transform, mixer or sprite APIs.
"""

from __future__ import annotations

import math
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402


Color = tuple[int, int, int]
BACKGROUND: Color = (10, 14, 26)


class GraphicsError(RuntimeError):
    """Report a display initialization failure in player-readable language."""


@dataclass(frozen=True)
class InputEvent:
    """Represent a platform-independent window or keyboard event."""

    kind: str
    key: str = ""
    text: str = ""


class Graphics:
    """Own the display, pixel buffers, keyboard input and frame clock."""

    def __init__(self) -> None:
        """Open the arcade window without initializing any sound subsystem."""
        self.width = 1000
        self.height = 850
        self._fonts: dict[int, pygame.font.Font] = {}
        self._sprites: dict[tuple[object, ...], pygame.Surface] = {}
        self._layers: dict[str, pygame.Surface] = {}
        try:
            pygame.display.init()
            pygame.font.init()
            desktop = pygame.display.Info()
            self._scale = min(
                1.0, max(640, desktop.current_w - 60) / self.width,
                max(544, desktop.current_h - 100) / self.height,
            )
            pygame.display.set_caption("PAC-MAN 42 | Maze Chase")
            self.screen = pygame.display.set_mode((
                round(self.width * self._scale),
                round(self.height * self._scale),
            ))
            self._clock = pygame.time.Clock()
            pygame.key.start_text_input()
        except pygame.error as exc:
            pygame.font.quit()
            pygame.display.quit()
            raise GraphicsError(
                "Cannot open the game window. Use a graphical Linux desktop "
                "and make sure its display is available."
            ) from exc

    def events(self) -> list[InputEvent]:
        """Read close, key and text events using stable application names."""
        result: list[InputEvent] = []
        pending = pygame.event.get()
        has_text = any(event.type == pygame.TEXTINPUT for event in pending)
        names = {
            "return": "enter",
            "keypad enter": "enter",
            "esc": "escape",
            " ": "space",
        }
        for event in pending:
            if event.type == pygame.QUIT:
                result.append(InputEvent("quit"))
            elif event.type == pygame.KEYDOWN:
                key = pygame.key.name(event.key).lower()
                result.append(InputEvent("key", names.get(key, key)))
                value = getattr(event, "unicode", "")
                if not has_text and value and value.isprintable():
                    result.append(InputEvent("text", text=value))
            elif event.type == pygame.TEXTINPUT:
                result.append(InputEvent("text", text=event.text))
        return result

    def begin(self) -> None:
        """Clear the frame's image buffer before the next complete redraw."""
        self.screen.fill(BACKGROUND)

    def rect(
        self, x: int, y: int, w: int, h: int, color: Color
    ) -> None:
        """Write a rectangular run of pixels into the frame buffer."""
        if w > 0 and h > 0:
            left = round(x * self._scale)
            top = round(y * self._scale)
            right = round((x + w) * self._scale)
            bottom = round((y + h) * self._scale)
            self.screen.fill(color, (
                left, top, max(1, right - left), max(1, bottom - top),
            ))

    def line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: Color,
        width: int = 1,
    ) -> None:
        """Rasterize a line using Bresenham's integer pixel algorithm."""
        if x1 == x2 or y1 == y2:
            half = max(0, width // 2)
            self.rect(min(x1, x2) - half, min(y1, y2) - half,
                      abs(x2 - x1) + width, abs(y2 - y1) + width, color)
            return
        dx = abs(x2 - x1)
        sx = 1 if x1 < x2 else -1
        dy = -abs(y2 - y1)
        sy = 1 if y1 < y2 else -1
        error = dx + dy
        half = max(0, width // 2)
        while True:
            self.rect(x1 - half, y1 - half, width, width, color)
            if x1 == x2 and y1 == y2:
                return
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x1 += sx
            if doubled <= dx:
                error += dx
                y1 += sy

    def circle(self, cx: int, cy: int, r: int, color: Color) -> None:
        """Rasterize a filled circle into horizontal pixel runs."""
        self.ellipse(cx, cy, r, r, color)

    def ellipse(
        self, cx: int, cy: int, rx: int, ry: int, color: Color
    ) -> None:
        """Rasterize a filled ellipse with clipped horizontal pixel spans."""
        if rx < 0 or ry < 0:
            return
        center_x, center_y = round(cx * self._scale), round(cy * self._scale)
        radius_x, radius_y = round(rx * self._scale), round(ry * self._scale)
        if radius_y == 0:
            self.screen.fill(
                color, (center_x - radius_x, center_y, 2 * radius_x + 1, 1)
            )
            return
        first = max(-radius_y, -center_y)
        last = min(radius_y, self.screen.get_height() - center_y - 1)
        for offset in range(first, last + 1):
            squared = max(0.0, 1.0 - (offset / radius_y) ** 2)
            span = int(radius_x * math.sqrt(squared))
            self.screen.fill(
                color, (center_x - span, center_y + offset, 2 * span + 1, 1)
            )

    def polygon(
        self, points: tuple[tuple[int, int], ...], color: Color
    ) -> None:
        """Fill a polygon using clipped even-odd pixel-center scanlines.

        Horizontal edges are skipped and vertical endpoints are half-open,
        so adjacent edges do not count their shared vertex twice. Concave
        silhouettes and shapes extending outside the window are supported.
        """
        if len(points) < 3:
            return
        scaled = tuple(
            (round(x * self._scale), round(y * self._scale))
            for x, y in points
        )
        edges = tuple(zip(scaled, scaled[1:] + scaled[:1]))
        first = max(0, min(y for _, y in scaled))
        last = min(self.screen.get_height(), max(y for _, y in scaled))
        screen_width = self.screen.get_width()
        for row in range(first, last):
            scan = row + 0.5
            crossings = sorted(
                x1 + (scan - y1) * (x2 - x1) / (y2 - y1)
                for (x1, y1), (x2, y2) in edges
                if (y1 <= scan < y2) or (y2 <= scan < y1)
            )
            for index in range(0, len(crossings) - 1, 2):
                left = max(0, math.ceil(crossings[index] - 0.5))
                right = min(
                    screen_width, math.ceil(crossings[index + 1] - 0.5)
                )
                if right > left:
                    self.screen.fill(color, (left, row, right - left, 1))

    def gradient(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        top: Color,
        bottom: Color,
    ) -> None:
        """Fill horizontal pixel rows with a vertical RGB color gradient."""
        if w <= 0 or h <= 0:
            return
        left, upper = round(x * self._scale), round(y * self._scale)
        width = max(1, round((x + w) * self._scale) - left)
        height = max(1, round((y + h) * self._scale) - upper)
        first = max(0, upper)
        last = min(self.screen.get_height(), upper + height)
        for row in range(first, last):
            blend = (row - upper) / max(1, height - 1)
            color = (
                round(top[0] + (bottom[0] - top[0]) * blend),
                round(top[1] + (bottom[1] - top[1]) * blend),
                round(top[2] + (bottom[2] - top[2]) * blend),
            )
            self.screen.fill(color, (left, row, width, 1))

    def cached_layer(self, key: str, paint: Callable[[], None]) -> None:
        """Paint an opaque scene once, then copy its saved image each frame.

        Failed painters leave the active buffer and cache intact. At most
        eight named layers are retained; shutdown releases every layer.
        """
        layer = self._layers.get(key)
        if layer is None:
            original = self.screen
            layer = pygame.Surface(original.get_size()).convert()
            layer.fill(BACKGROUND)
            try:
                self.screen = layer
                paint()
            finally:
                self.screen = original
            if len(self._layers) >= 8:
                del self._layers[next(iter(self._layers))]
            self._layers[key] = layer
        self.screen.blit(layer, (0, 0))

    def text(
        self,
        text: str,
        x: int,
        y: int,
        size: int = 22,
        color: Color = (231, 237, 251),
        center: bool = False,
    ) -> None:
        """Place a text image, corresponding to MLX's string placement."""
        x, y = round(x * self._scale), round(y * self._scale)
        size = max(10, round(size * self._scale))
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        buffer = self._fonts[size].render(str(text), True, color)
        if center:
            x -= buffer.get_width() // 2
        self.screen.blit(buffer, (x, y))

    def player(
        self,
        cx: int,
        cy: int,
        radius: int,
        direction: str = "RIGHT",
        phase: int = 1,
        color: Color = (255, 214, 66),
    ) -> None:
        """Copy a cached, hand-rasterized Pac-Man image into the frame."""
        cx, cy = round(cx * self._scale), round(cy * self._scale)
        radius = max(2, round(radius * self._scale))
        key = ("player", radius, direction, phase, color)
        if key not in self._sprites:
            size = radius * 2 + 3
            buffer = pygame.Surface((size, size), pygame.SRCALPHA)
            angle = {
                "RIGHT": 0.0,
                "DOWN": math.pi / 2,
                "LEFT": math.pi,
                "UP": -math.pi / 2,
            }.get(direction, 0.0)
            opening = (0.10, 0.35, 0.60, 0.35)[phase % 4]
            for y in range(-radius, radius + 1):
                for x in range(-radius, radius + 1):
                    if x * x + y * y > radius * radius:
                        continue
                    relative = math.atan2(y, x) - angle
                    relative = (relative + math.pi) % math.tau - math.pi
                    if abs(relative) >= opening:
                        buffer.set_at((x + radius + 1, y + radius + 1), color)
            self._sprites[key] = buffer
        self.screen.blit(
            self._sprites[key], (cx - radius - 1, cy - radius - 1)
        )

    def ghost(
        self,
        cx: int,
        cy: int,
        radius: int,
        color: Color,
        direction: str = "LEFT",
        frightened: bool = False,
        phase: int = 0,
    ) -> None:
        """Copy a generated ghost image with a scalloped body and eyes."""
        cx, cy = round(cx * self._scale), round(cy * self._scale)
        radius = max(2, round(radius * self._scale))
        key = ("ghost", radius, color, direction, frightened, phase % 2)
        if key not in self._sprites:
            size = radius * 2 + 3
            buffer = pygame.Surface((size, size), pygame.SRCALPHA)
            for y in range(-radius, radius + 1):
                for x in range(-radius, radius + 1):
                    cap = y <= 0 and x * x + y * y <= radius * radius
                    body = 0 < y < radius - 2
                    skirt = y >= radius - 2 and (
                        (x + radius + phase) // max(2, radius // 2) % 2 == 0
                    )
                    if cap or body or skirt:
                        buffer.set_at((x + radius + 1, y + radius + 1), color)
            self._ghost_face(buffer, radius, direction, frightened)
            self._sprites[key] = buffer
        self.screen.blit(
            self._sprites[key], (cx - radius - 1, cy - radius - 1)
        )

    def eyes(
        self,
        cx: int,
        cy: int,
        radius: int,
        direction: str = "LEFT",
    ) -> None:
        """Copy cached, hand-rasterized eyes for a harmless eaten ghost."""
        cx, cy = round(cx * self._scale), round(cy * self._scale)
        radius = max(3, round(radius * self._scale))
        key = ("eyes", radius, direction)
        if key not in self._sprites:
            size = radius * 2 + 3
            buffer = pygame.Surface((size, size), pygame.SRCALPHA)
            origin = radius + 1
            gap = max(2, round(radius * .44))
            rx, ry = max(2, round(radius * .32)), max(2, round(radius * .45))
            shift_x, shift_y = {
                "UP": (0, -1), "RIGHT": (1, 0),
                "DOWN": (0, 1), "LEFT": (-1, 0),
            }.get(direction, (0, 0))
            pupil = max(1, radius // 6)
            for sign in (-1, 1):
                eye_x = origin + sign * gap
                for y in range(-ry, ry + 1):
                    for x in range(-rx, rx + 1):
                        inside = x * x * ry * ry + y * y * rx * rx
                        if inside <= rx * rx * ry * ry:
                            buffer.set_at((eye_x + x, origin + y),
                                          (239, 249, 255))
                for y in range(-pupil, pupil + 1):
                    for x in range(-pupil, pupil + 1):
                        if x * x + y * y <= pupil * pupil:
                            buffer.set_at((eye_x + x + shift_x,
                                           origin + y + shift_y),
                                          (52, 112, 211))
            self._sprites[key] = buffer
        self.screen.blit(
            self._sprites[key], (cx - radius - 1, cy - radius - 1)
        )

    @staticmethod
    def _ghost_face(
        buffer: pygame.Surface,
        radius: int,
        direction: str,
        frightened: bool,
    ) -> None:
        """Write a tiny eye or frightened-face pattern into a ghost image."""
        origin = radius + 1
        eye = max(1, radius // 4)
        if frightened:
            for sign in (-1, 1):
                buffer.fill(
                    (235, 245, 255),
                    (origin + sign * eye * 2 - 1, origin - eye, 2, 2),
                )
            for x in range(-eye * 2, eye * 2 + 1):
                buffer.set_at(
                    (origin + x, origin + eye + abs(x) % 2),
                    (235, 245, 255),
                )
            return
        shift = {
            "UP": (0, -1),
            "RIGHT": (1, 0),
            "DOWN": (0, 1),
            "LEFT": (-1, 0),
        }.get(direction, (0, 0))
        for sign in (-1, 1):
            x = origin + sign * eye * 2 - eye
            y = origin - eye * 2
            buffer.fill((248, 250, 255), (x, y, eye * 2 + 1, eye * 3))
            buffer.fill(
                (16, 28, 70),
                (x + eye + shift[0], y + eye + shift[1], eye, eye + 1),
            )

    def present(self) -> None:
        """Copy the completed frame to the visible window."""
        pygame.display.flip()

    def tick(self) -> float:
        """Pace the loop to sixty frames per second and return elapsed time."""
        return self._clock.tick(60) / 1000.0

    def save_screenshot(self, path: Path) -> None:
        """Save the current pixel buffer for developer visual verification."""
        pygame.image.save(self.screen, str(path))

    def close(self) -> None:
        """Release the text input, font and display resources."""
        if pygame.display.get_init():
            pygame.key.stop_text_input()
        self._sprites.clear()
        self._fonts.clear()
        self._layers.clear()
        pygame.font.quit()
        pygame.display.quit()
