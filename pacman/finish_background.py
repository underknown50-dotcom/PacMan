"""Draw original victory and loss gardens with cached raster scenery."""

from __future__ import annotations

import math
import time

from .graphics import Color, Graphics


GOLD: Color = (255, 218, 118)
LEAVES: tuple[Color, ...] = (
    (237, 200, 103), (160, 194, 119), (220, 219, 156), (93, 157, 121),
)


def _blend(first: Color, second: Color, amount: float) -> Color:
    """Interpolate RGB channels for code-generated atmospheric scenery."""
    return (
        round(first[0] + (second[0] - first[0]) * amount),
        round(first[1] + (second[1] - first[1]) * amount),
        round(first[2] + (second[2] - first[2]) * amount),
    )


class FinishBackground:
    """Keep decorative finish animation independent of gameplay and its RNG."""

    def __init__(self, graphics: Graphics) -> None:
        """Remember the raster facade and a monotonic presentation clock."""
        self.g = graphics
        self._started = time.monotonic()

    def draw(self, victory: bool, elapsed: float | None = None) -> None:
        """Copy static scenery and add subtle, elapsed-time moving details."""
        now = time.monotonic() - self._started if elapsed is None else elapsed
        if victory:
            self.g.cached_layer("finish-victory-garden-v1", self._victory)
            self._celebration(now)
        else:
            self.g.cached_layer("finish-loss-garden-v1", self._loss)
            self._rain(now)

    def _hills(
        self, base: int, amplitude: int, phase: float, color: Color,
    ) -> None:
        """Rasterize one curved, layered garden silhouette into its cache."""
        ridge = tuple(
            (x, round(base + math.sin(x / 160 + phase) * amplitude))
            for x in range(-20, 1021, 12)
        )
        self.g.polygon((*ridge, (1020, 850), (-20, 850)), color)

    def _halo(
        self,
        cx: int,
        cy: int,
        radius: int,
        sky_top: Color,
        sky_bottom: Color,
        tint: Color,
    ) -> None:
        """Blend a rim-free radial glow into the sky's actual gradient."""
        for y in range(max(0, cy - radius), min(850, cy + radius), 2):
            sky = _blend(sky_top, sky_bottom, y / 849)
            for x in range(max(0, cx - radius), min(1000, cx + radius), 2):
                distance = math.hypot(x - cx, y - cy)
                if distance < radius:
                    strength = (1 - distance / radius) ** 2 * .7
                    self.g.rect(x, y, 2, 2, _blend(sky, tint, strength))

    def _victory(self) -> None:
        """Paint a sunlit green garden, golden path, shrubs and flowers."""
        g = self.g
        g.gradient(0, 0, 1000, 850, (13, 35, 34), (58, 94, 56))
        self._halo(824, 167, 124, (13, 35, 34), (58, 94, 56),
                   (238, 209, 124))
        g.circle(824, 167, 47, (229, 214, 156))
        g.circle(813, 156, 36, (244, 229, 180))
        self._hills(360, 33, .4, (35, 73, 57))
        self._hills(456, 31, 2.2, (29, 81, 56))
        g.gradient(0, 590, 1000, 260, (25, 67, 47), (9, 34, 29))
        g.polygon(((477, 567), (522, 567), (673, 850), (316, 850)),
                  (80, 99, 62))
        g.polygon(((488, 567), (508, 567), (619, 850), (369, 850)),
                  (130, 128, 78))
        for x, y, rx in ((495, 773, 58), (497, 809, 73), (499, 846, 84)):
            g.ellipse(x, y, rx, 8, (170, 157, 103))
        for side in (-1, 1):
            anchor = 70 if side == -1 else 930
            g.polygon(((anchor - 10, 780), (anchor + 14, 780),
                       (anchor + side * 16, 338),
                       (anchor + side * 4, 286)), (48, 78, 51))
            for index in range(5):
                y = 350 + index * 77
                x = anchor + round(math.sin(index * 1.3) * 15)
                g.ellipse(x + side * 35, y, 84, 53, (32, 83, 54))
                g.ellipse(x - side * 13, y - 18, 62, 44,
                          (48 + index * 3, 106 + index * 3, 64))
        for index in range(23):
            x = (index * 113 + 27) % 1000
            if 235 < x < 765:
                continue
            y = 747 + (index * 29) % 95
            g.ellipse(x, y + 17, 38, 18, (21, 66, 43))
            g.line(x, y + 14, x + 3, y - 7, (96, 137, 75), 2)
            for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)):
                g.circle(x + 3 + dx, y - 7 + dy, 4, (211, 192, 125))
            g.circle(x + 3, y - 7, 2, (249, 218, 123))

    def _loss(self) -> None:
        """Paint a moonlit indigo garden with bare branches and wet stones."""
        g = self.g
        g.gradient(0, 0, 1000, 850, (10, 15, 35), (33, 48, 76))
        self._halo(831, 158, 113, (10, 15, 35), (33, 48, 76),
                   (139, 161, 198))
        g.circle(831, 158, 39, (167, 184, 213))
        g.circle(844, 146, 36, (35, 45, 68))
        for index in range(22):
            x = 31 + (index * 139) % 940
            y = 82 + (index * 67) % 260
            g.rect(x, y, 2, 2, (83, 105, 145))
        self._hills(395, 30, 1.8, (23, 34, 58))
        self._hills(505, 27, .3, (20, 33, 53))
        g.gradient(0, 608, 1000, 242, (17, 30, 48), (8, 17, 30))
        g.polygon(((484, 572), (518, 572), (681, 850), (323, 850)),
                  (39, 51, 69))
        g.polygon(((492, 572), (506, 572), (617, 850), (380, 850)),
                  (49, 62, 81))
        for x, y, rx in ((502, 779, 57), (494, 819, 71), (502, 850, 85)):
            g.ellipse(x, y, rx, 6, (66, 81, 104))
        for side in (-1, 1):
            anchor = 78 if side == -1 else 948
            g.polygon(((anchor - 13, 812), (anchor + 11, 812),
                       (anchor + side * 13, 454),
                       (anchor + side * 6, 241),
                       (anchor - side * 3, 273)), (18, 30, 49))
            for index in range(6):
                y = 327 + index * 63
                reach = 47 + index * 3
                g.line(anchor, y + 46, anchor - side * reach, y - 9,
                       (31, 47, 68), 5)
                g.line(anchor - side * (reach - 10), y + 4,
                       anchor - side * (reach - 5), y - 35,
                       (31, 47, 68), 3)
        for index in range(14):
            x = index * 79 - 6
            if 265 < x < 735:
                continue
            g.ellipse(x, 797 + (index * 17) % 47, 66, 24, (14, 30, 43))
        for x, y, rx in ((133, 758, 67), (864, 781, 91)):
            g.ellipse(x, y, rx, 10, (28, 48, 68))
            g.ellipse(x + 8, y - 2, rx - 22, 3, (57, 77, 100))

    def _celebration(self, now: float) -> None:
        """Drift small gold leaves and fireflies along the garden's edges."""
        g = self.g
        for index in range(35):
            origin = (index * 137 + 41) % 1000
            x = round(origin + math.sin(now * .4 + index) * 17)
            y = round((index * 73 + now * (7 + index % 4)) % 856 - 3)
            if 204 < x < 796 and 330 < y < 738:
                continue
            color = LEAVES[index % len(LEAVES)]
            sway = round(math.sin(now * .9 + index) * 3)
            g.polygon(((x - 3, y), (x + sway, y - 4),
                       (x + 3, y), (x - sway, y + 4)), color)
        for index in range(12):
            x = 45 + (index * 83) % 930
            y = round(280 + (index * 47) % 430
                      + math.sin(now * .55 + index) * 12)
            glow = .5 + math.sin(now * .7 + index) * .2
            g.circle(x, y, 3, _blend((44, 78, 52), (128, 145, 82), glow))
            g.circle(x, y, 1, (240, 221, 148))

    def _rain(self, now: float) -> None:
        """Move soft clouds and short rain strokes outside the result form."""
        g = self.g
        for origin, y, speed in ((-60, 172, 5.0), (578, 94, 3.1)):
            x = round((origin + now * speed) % 1410 - 180)
            g.ellipse(x, y, 119, 11, (29, 40, 63))
            g.ellipse(x + 29, y - 6, 73, 12, (31, 43, 67))
        for index in range(42):
            side = index % 2
            x = 13 + (index * 43) % 159 + side * 817
            y = round((index * 89 + now * (63 + index % 5 * 11)) % 890 - 24)
            g.line(x, y, x - 4, y + 13, (58, 78, 109))
        for index, (x, y) in enumerate(((132, 759), (864, 781))):
            radius = 6 + int((now * 11 + index * 7) % 41)
            g.ellipse(x, y, radius, max(1, radius // 6), (51, 72, 96))
            g.ellipse(x, y - 1, max(1, radius - 2),
                      max(0, radius // 6 - 1), (28, 48, 68))

    def emblem(self, victory: bool, cx: int, cy: int) -> None:
        """Draw a trophy for victory or a resting arcade badge for a loss."""
        g = self.g
        if not victory:
            g.circle(cx, cy, 37, (35, 53, 79))
            g.circle(cx, cy, 34, (19, 35, 57))
            g.player(cx, cy, 23, "RIGHT", 0, (179, 199, 222))
            g.circle(cx + 7, cy - 9, 2, (23, 42, 68))
            return
        g.ellipse(cx, cy + 35, 52, 8, (17, 48, 33))
        g.ellipse(cx, cy - 15, 44, 32, (166, 122, 48))
        g.ellipse(cx, cy - 18, 34, 22, (32, 63, 42))
        g.polygon(((cx - 29, cy - 34), (cx + 29, cy - 34),
                   (cx + 22, cy + 3), (cx + 10, cy + 15),
                   (cx - 10, cy + 15), (cx - 22, cy + 3)),
                  (240, 190, 76))
        g.polygon(((cx - 22, cy - 30), (cx + 4, cy - 30),
                   (cx + 4, cy + 7), (cx - 9, cy + 10),
                   (cx - 17, cy + 1)), (255, 219, 119))
        g.rect(cx - 5, cy + 12, 10, 17, (229, 174, 65))
        g.rect(cx - 24, cy + 28, 48, 7, (241, 198, 93))
        g.rect(cx - 29, cy + 34, 58, 5, (175, 128, 51))
        g.circle(cx + 49, cy - 38, 2, GOLD)
        g.line(cx + 49, cy - 44, cx + 49, cy - 32, GOLD)
        g.line(cx + 43, cy - 38, cx + 55, cy - 38, GOLD)
