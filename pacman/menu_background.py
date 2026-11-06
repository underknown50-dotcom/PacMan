"""Paint a gently animated garden using MLX-equivalent image operations."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
import time

from .graphics import Color, Graphics


@dataclass(frozen=True)
class Firefly:
    """Describe one independently drifting, softly glowing garden light."""

    x: float
    y: float
    phase: float
    speed: float


def _mix(first: Color, second: Color, amount: float) -> Color:
    """Blend RGB channels without requiring a platform graphics effect."""
    return (
        round(first[0] + (second[0] - first[0]) * amount),
        round(first[1] + (second[1] - first[1]) * amount),
        round(first[2] + (second[2] - first[2]) * amount),
    )


class GardenBackground:
    """Separate cached scenery from time-based foliage, water and lights."""

    def __init__(self, graphics: Graphics) -> None:
        """Prepare local decorative variation without touching gameplay RNG."""
        self.g = graphics
        self._started = time.monotonic()
        rng = random.Random(142)
        self._fireflies = tuple(
            Firefly(rng.uniform(480, 1010), rng.uniform(310, 770),
                    rng.uniform(0, math.tau), rng.uniform(.35, .7))
            for _ in range(26)
        )
        self._grass = tuple(
            (rng.choice((rng.uniform(-20, 185), rng.uniform(875, 1020))),
             rng.uniform(807, 878), rng.uniform(35, 90),
             rng.uniform(0, math.tau))
            for _ in range(28)
        )

    def draw(self, elapsed: float | None = None) -> None:
        """Paint an elapsed-time animation independent of game simulation."""
        now = time.monotonic() - self._started if elapsed is None else elapsed
        self.g.cached_layer("main-menu-garden-v1", self._landscape)
        self._clouds(now)
        self._tree(now)
        self._water(now)
        self._lantern(now)
        self._flowers(now)
        self._lights(now)
        self._foreground(now)

    def _landscape(self) -> None:
        """Rasterize the static sky, moon, garden path and pond just once."""
        g = self.g
        g.gradient(0, 0, 1000, 850, (10, 28, 43), (48, 103, 96))
        # Blend a radial glow into the sky itself, with no visible outer rim.
        for y in range(40, 282, 2):
            sky = _mix((10, 28, 43), (48, 103, 96), y / 849)
            for x in range(691, 933, 2):
                distance = math.hypot(x - 811, y - 160)
                if distance <= 120:
                    amount = (1 - distance / 120) ** 2 * .45
                    g.rect(x, y, 2, 2, _mix(sky, (163, 182, 145), amount))
        g.circle(811, 160, 56, (223, 228, 187))
        g.circle(797, 148, 43, (234, 236, 200))
        for index in range(16):
            x = 515 + (index * 137) % 460
            y = 82 + (index * 67) % 180
            g.circle(x, y, 1, (117, 162, 155))
        for base, amplitude, phase, color in (
            (358, 34, 0.0, (35, 83, 83)),
            (403, 30, 1.4, (30, 91, 81)),
            (463, 26, 2.7, (25, 82, 65)),
        ):
            ridge = tuple(
                (x, round(base + math.sin(x / 175 + phase) * amplitude))
                for x in range(-20, 1021, 10)
            )
            g.polygon((*ridge, (1020, 850), (-20, 850)), color)
        g.gradient(0, 520, 1000, 330, (23, 74, 61), (10, 39, 37))
        self._distant_plants()
        g.polygon((
            (681, 423), (700, 429), (657, 486), (632, 550),
            (640, 616), (678, 687), (740, 758), (807, 850),
            (518, 850), (576, 754), (600, 681), (601, 605),
            (611, 532), (644, 468),
        ), (53, 89, 74))
        g.polygon((
            (683, 431), (689, 430), (650, 490), (624, 554),
            (633, 623), (666, 692), (722, 766), (774, 850),
            (557, 850), (592, 754), (613, 681), (611, 606),
            (621, 536), (652, 471),
        ), (74, 108, 89))
        for x, y, rx, ry in (
            (636, 795, 53, 12), (637, 736, 40, 9),
            (625, 684, 29, 7), (620, 635, 24, 6),
            (623, 588, 18, 5), (632, 549, 14, 4),
            (645, 510, 11, 3),
        ):
            g.ellipse(x, y + 2, rx, ry, (55, 86, 73))
            g.ellipse(x, y, rx, max(2, ry - 1), (104, 132, 109))
        g.ellipse(854, 733, 181, 77, (37, 78, 66))
        g.ellipse(854, 729, 171, 68, (16, 62, 66))
        g.ellipse(854, 719, 153, 49, (21, 77, 77))
        g.ellipse(869, 700, 100, 22, (25, 84, 82))
        # A small reflected moon and lilies make the water read as a pond.
        g.ellipse(855, 716, 22, 4, (102, 137, 111))
        for x, y, radius in ((742, 741, 14), (931, 751, 18),
                             (955, 715, 11)):
            g.ellipse(x, y, radius, max(3, radius // 3), (52, 115, 78))
            g.line(x, y, x + radius, y - 2, (22, 76, 64))
        g.ellipse(935, 744, 7, 3, (232, 196, 169))
        # The focal tree trunk and its branches stay rooted as leaves sway.
        g.polygon(((848, 506), (865, 506), (859, 354), (865, 291),
                   (853, 281), (849, 359)), (58, 90, 75))
        g.polygon(((853, 372), (818, 313), (793, 289), (800, 282),
                   (831, 309), (860, 351)), (65, 100, 80))
        g.polygon(((856, 354), (891, 308), (920, 290), (917, 281),
                   (885, 302), (851, 337)), (65, 100, 80))
        g.line(858, 489, 855, 375, (98, 126, 91), 2)
        g.ellipse(855, 507, 44, 9, (19, 56, 49))
        g.rect(550, 487, 4, 137, (49, 85, 71))
        g.ellipse(552, 624, 20, 4, (15, 49, 42))

    def _distant_plants(self) -> None:
        """Give the garden depth with calm tree and shrub silhouettes."""
        g = self.g
        for x, y, size in ((47, 447, 78), (160, 462, 50),
                           (528, 433, 31), (980, 467, 65)):
            g.polygon(((x - 5, y + 105), (x + 7, y + 105),
                       (x + 3, y - 8), (x - 3, y - 8)), (26, 65, 59))
            for dx, dy, radius in ((-28, -6, .7), (28, -14, .8),
                                   (0, -46, .9)):
                g.ellipse(x + dx, y + dy, round(size * radius),
                          round(size * radius * .8), (27, 74, 64))
        for index in range(21):
            x = index * 52 - 15
            y = round(530 + 15 * math.sin(index * 1.4))
            g.ellipse(x, y, 44, 28, (20, 64, 52))
            g.ellipse(x - 9, y - 5, 27, 24, (27, 78, 58))
        for x, y, rx in ((38, 739, 90), (148, 766, 79),
                         (291, 785, 53), (982, 820, 84)):
            g.ellipse(x, y, rx, 40, (18, 62, 47))
            g.ellipse(x - 16, y - 12, rx - 10, 27, (30, 83, 54))

    def _clouds(self, now: float) -> None:
        """Drift a few soft cloud banks slowly across the distant sky."""
        for origin, y, speed in ((520, 103, 3.1), (1080, 275, 2.2)):
            x = round((origin + now * speed) % 1460 - 170)
            self.g.ellipse(x, y, 105, 11, (41, 76, 84))
            self.g.ellipse(x + 22, y - 7, 61, 12, (43, 79, 87))

    def _tree(self, now: float) -> None:
        """Sway broad canopy clusters and their hanging leaf fronds."""
        g = self.g
        sway = math.sin(now * .68) * 3.2
        for index, (x, y, rx, ry, color) in enumerate((
            (786, 265, 67, 48, (25, 84, 66)),
            (910, 255, 71, 51, (29, 92, 69)),
            (854, 207, 73, 55, (39, 111, 77)),
            (819, 231, 60, 47, (46, 124, 82)),
            (874, 245, 79, 57, (44, 119, 76)),
            (843, 285, 74, 39, (32, 100, 69)),
        )):
            dx = round(sway + math.sin(now * .8 + index) * 1.5)
            g.ellipse(x + dx, y, rx, ry, color)
        for index in range(12):
            x = 761 + index * 16 + (index % 3 - 1) * 3
            length = 25 + (index * 17) % 52
            top = round(287 + math.sin(index * .8) * 13)
            lean = math.sin(now * .9 + index * .55) * 7
            for segment in range(5):
                fraction = segment / 4
                px = round(x + sway + lean * fraction * fraction)
                py = round(top + length * fraction)
                g.ellipse(px, py, 4, 7, (54, 122, 78))
            g.ellipse(round(x + sway + lean), top + length, 3, 6,
                      (91, 151, 94))
        for index in range(14):
            x = 778 + (index * 37) % 146
            y = 211 + (index * 23) % 74
            g.ellipse(round(x + sway), y, 5, 2, (83, 143, 92))
        for x, y, rx, ry, color in (
            (795, 199, 17, 11, (47, 124, 81)),
            (826, 165, 19, 10, (47, 121, 80)),
            (868, 164, 15, 9, (48, 121, 80)),
            (906, 201, 18, 11, (40, 110, 75)),
            (921, 273, 17, 10, (39, 109, 74)),
        ):
            g.ellipse(round(x + sway), y, rx, ry, color)

    def _water(self, now: float) -> None:
        """Expand and fade curved water highlights without abrupt resets."""
        for index in range(4):
            phase = (now * .075 + index * .25) % 1
            strength = math.sin(phase * math.pi) * .5
            color = _mix((21, 77, 77), (105, 166, 140), strength)
            rx = 22 + phase * 116
            cy = 716 + index * 11
            points = tuple(
                (round(855 + math.cos(step * math.pi / 24) * rx),
                 round(cy + math.sin(step * math.pi / 24) * rx * .16))
                for step in range(25)
            )
            for first, second in zip(points, points[1:]):
                self.g.line(*first, *second, color)
        for index in range(5):
            x = round(814 + index * 19 + math.sin(now * .6 + index) * 5)
            y = 701 + index * 10
            self.g.ellipse(x, y, 8 - index, 1, (100, 144, 118))

    def _lantern(self, now: float) -> None:
        """Keep a warm garden lamp and its pool of light quietly luminous."""
        pulse = .85 + math.sin(now * .8) * .06
        for radius in range(28, 4, -3):
            amount = ((28 - radius) / 24) ** 2 * .6 * pulse
            color = _mix((24, 71, 57), (235, 194, 110), amount)
            self.g.circle(552, 483, radius, color)
        self.g.rect(544, 472, 16, 22, (42, 66, 52))
        self.g.rect(547, 476, 10, 13, (242, 217, 153))
        self.g.polygon(((541, 472), (552, 465), (563, 472)),
                       (70, 96, 67))
        self.g.ellipse(552, 636, 25, 4, (83, 111, 70))

    def _flowers(self, now: float) -> None:
        """Move slender flower stems gently around the garden's edges."""
        g = self.g
        for index, (x, y) in enumerate((
            (26, 731), (56, 751), (90, 734), (126, 772),
            (192, 773), (226, 758), (289, 783), (327, 777),
            (941, 809), (967, 789), (993, 805),
        )):
            height = 25 + (index * 13) % 22
            dx = math.sin(now * .85 + index * .75) * 3.5
            tip = (round(x + dx), y - height)
            g.line(x, y, *tip, (72, 127, 80), 2)
            g.ellipse(round(x + dx * .45) - 4, y - height // 2,
                      7, 3, (62, 116, 72))
            color = (197, 175, 213) if index % 3 else (229, 204, 145)
            for angle in range(5):
                direction = angle * math.tau / 5
                g.ellipse(round(tip[0] + math.cos(direction) * 3),
                          round(tip[1] + math.sin(direction) * 3),
                          3, 3, color)
            g.circle(*tip, 2, (244, 217, 142))

    def _lights(self, now: float) -> None:
        """Float fireflies with gradual glow changes instead of flashing."""
        for fly in self._fireflies:
            x = round(fly.x + math.sin(now * fly.speed + fly.phase) * 20)
            y = round(fly.y + math.cos(now * fly.speed * .7 + fly.phase) * 13)
            glow = .45 + .3 * math.sin(now * .8 + fly.phase)
            self.g.circle(x, y, 5, _mix((28, 76, 60), (84, 119, 72), glow))
            self.g.circle(x, y, 2, _mix((108, 149, 91), (230, 229, 157), glow))
            self.g.rect(x, y, 1, 1, (239, 238, 182))

    def _foreground(self, now: float) -> None:
        """Bend foreground grass with phase-offset, low-amplitude wind."""
        for index, (x, y, height, phase) in enumerate(self._grass):
            lean = math.sin(now * .8 + phase) * 8
            self.g.polygon((
                (round(x - 2), round(y)), (round(x + 2), round(y)),
                (round(x + lean + 6), round(y - height)),
                (round(x + lean * .5), round(y - height * .55)),
            ), (35 + index % 3 * 8, 91 + index % 4 * 7, 64))
