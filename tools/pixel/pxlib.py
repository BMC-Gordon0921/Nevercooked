"""Pixel-art primitives for the bright space-canteen restyle.

Every sprite is drawn pixel by pixel with ordinary arithmetic colours, then
snapped to a *short ramp* of data/palette.json entries: each finished image
uses at most MAX_COLORS distinct RGB values, and every one of them is a
palette colour. That keeps the set coherent and enforces the 12-colour cap.
"""
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from core import config

MAX_COLORS = 12
PALETTE = {name: config.hex_rgb(value) for name, value in config.PALETTE.items()}
TILE = 64


# --------------------------------------------------------------- colour maths
def col(name):
    return PALETTE[name]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t + 0.5) for i in range(3))


def li(c, t):
    return mix(c, (255, 255, 255), t)


def dk(c, t):
    return mix(c, PALETTE["ink"], t)


def warm(c, t):
    return mix(c, PALETTE["roast"], t)


# ------------------------------------------------------------------- hashing
def h2(x, y, seed=0):
    """Deterministic 0..1 hash for stable per-pixel noise."""
    n = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def h3(x, y, z, seed=0):
    return h2(x + z * 97, y + z * 31, seed)


# --------------------------------------------------------------------- canvas
class Art:
    def __init__(self, w, h):
        self.w, self.h = int(w), int(h)
        self.s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)

    # -- raw ------------------------------------------------------------
    def fill(self, c):
        self.s.fill((*c, 255))

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.s.set_at((x, y), (int(c[0]), int(c[1]), int(c[2]), 255))

    def rect(self, x, y, w, h, c):
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            return
        pygame.draw.rect(self.s, (int(c[0]), int(c[1]), int(c[2]), 255), pygame.Rect(x, y, w, h))

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1 - x0 + 1, 1, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, 1, y1 - y0 + 1, c)

    def ellipse(self, x, y, w, h, c):
        if w <= 0 or h <= 0:
            return
        pygame.draw.ellipse(self.s, (int(c[0]), int(c[1]), int(c[2]), 255),
                            pygame.Rect(int(x), int(y), int(w), int(h)))

    def ring(self, x, y, w, h, c, t=1):
        pygame.draw.ellipse(self.s, (int(c[0]), int(c[1]), int(c[2]), 255),
                            pygame.Rect(int(x), int(y), int(w), int(h)), int(t))

    def poly(self, points, c):
        pygame.draw.polygon(self.s, (int(c[0]), int(c[1]), int(c[2]), 255),
                            [(int(p[0]), int(p[1])) for p in points])

    def line(self, p0, p1, c):
        pygame.draw.line(self.s, (int(c[0]), int(c[1]), int(c[2]), 255),
                         (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])))

    def blit(self, other, x, y):
        self.s.blit(other.s if isinstance(other, Art) else other, (int(x), int(y)))

    # -- shape helpers ---------------------------------------------------
    def rrect(self, x, y, w, h, c, r=2):
        """Hard-edged rounded rectangle (no anti-aliasing)."""
        x, y, w, h, r = int(x), int(y), int(w), int(h), int(r)
        if w <= 0 or h <= 0:
            return
        r = min(r, w // 2, h // 2)
        self.rect(x + r, y, w - 2 * r, h, c)
        for i in range(r):
            inset = r - i
            self.hline(x + r - inset, x + w - 1 - r + inset, y + i, c)
            self.hline(x + r - inset, x + w - 1 - r + inset, y + h - 1 - i, c)

    def slab(self, x, y, w, h, base, top=0.18, bot=0.24, left=0.06, right=0.12):
        """Three-tone volume block: bright top, base middle, dark bottom."""
        self.rect(x, y, w, h, base)
        self.hline(x, x + w - 1, y, li(base, top))
        if h > 3:
            self.hline(x, x + w - 1, y + 1, mix(base, li(base, top), 0.55))
        self.rect(x, y + h - max(2, int(h * bot)), w, max(2, int(h * bot)), dk(base, bot + 0.2))
        self.vline(x, y, y + h - 1, li(base, left))
        self.vline(x + w - 1, y, y + h - 1, dk(base, right))

    def frame(self, x, y, w, h, c_light, c_dark, t=1):
        """Inset bevel frame: light along the top/left, dark along bottom/right."""
        for i in range(t):
            self.hline(x + i, x + w - 1 - i, y + i, c_light)
            self.vline(x + i, y + i, y + h - 1 - i, c_light)
            self.hline(x + i, x + w - 1 - i, y + h - 1 - i, c_dark)
            self.vline(x + w - 1 - i, y + i, y + h - 1 - i, c_dark)

    def vgrad(self, x, y, w, h, c_top, c_bot):
        for i in range(h):
            self.hline(x, x + w - 1, y + i, mix(c_top, c_bot, i / max(1, h - 1)))

    # -- details ---------------------------------------------------------
    def rivet(self, x, y, hi=None, lo=None, base=None):
        hi = hi or col("silver")
        lo = lo or dk(col("steel"), 0.45)
        base = base or col("steel")
        self.rect(x, y, 2, 2, base)
        self.px(x, y, hi)
        self.px(x + 1, y + 1, lo)

    def lamp(self, x, y, c, lit=True):
        """3x3 indicator with a dark bezel and a hot centre."""
        self.rect(x - 1, y - 1, 3, 3, dk(c, 0.55))
        self.rect(x, y, 2, 2, c if lit else dk(c, 0.35))
        if lit:
            self.px(x, y, li(c, 0.65))

    def vents(self, x, y, w, h, base, step=3):
        self.rect(x, y, w, h, dk(base, 0.30))
        for i in range(0, h, step):
            self.hline(x, x + w - 1, y + i, dk(base, 0.55))
            if i + 1 < h:
                self.hline(x, x + w - 1, y + i + 1, li(base, 0.22))

    def screen(self, x, y, w, h, glow, base=None, rows=3):
        base = base or dk(col("slate"), 0.15)
        self.rect(x, y, w, h, base)
        self.frame(x, y, w, h, dk(self.s.get_at((x, y))[:3], 0.0) if False else li(base, 0.25), dk(base, 0.45))
        for r in range(rows):
            yy = y + 2 + r * 3
            if yy >= y + h - 1:
                break
            wid = max(2, w - 4 - r * 2)
            self.hline(x + 2, x + 1 + wid, yy, glow if r % 2 == 0 else mix(glow, base, 0.45))

    def steam(self, cx, y_top, height, light, mid, seed=0, width=2, phase=0.0):
        """A thin rising wisp: 1-2px core with a lighter cap."""
        for i in range(height):
            y = y_top + height - 1 - i
            t = i / max(1, height - 1)
            off = math.sin(i * 0.55 + seed * 1.7 + phase) * (1.0 + 1.6 * t)
            x = int(round(cx + off))
            c = mid if t < 0.45 else light
            self.hline(x, x + width - 1, y, c)
            if t > 0.55 and h2(x, y, seed) > 0.55:
                self.px(x + width, y, light)

    def grime(self, x, y, w, h, base, tint, density=0.05, seed=0, scale=1):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if h2(xx, yy, seed) < density:
                    self.px(xx, yy, mix(base, tint, 0.35 + 0.4 * h2(xx, yy, seed + 7)))


# ---------------------------------------------------------------- postprocess
def outline_out(art, c):
    """1px dark rim on the outside of the silhouette (keeps canvas size)."""
    w, h = art.w, art.h
    mask = [[art.s.get_at((x, y))[3] > 0 for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                continue
            near = ((x > 0 and mask[y][x - 1]) or (x < w - 1 and mask[y][x + 1])
                    or (y > 0 and mask[y - 1][x]) or (y < h - 1 and mask[y + 1][x])
                    or (x > 0 and y > 0 and mask[y - 1][x - 1])
                    or (x < w - 1 and y > 0 and mask[y - 1][x + 1])
                    or (x > 0 and y < h - 1 and mask[y + 1][x - 1])
                    or (x < w - 1 and y < h - 1 and mask[y + 1][x + 1]))
            if near:
                art.s.set_at((x, y), (*c, 255))


def quantize(art, ramp):
    """Snap every pixel to the nearest colour of a <=12 entry palette ramp."""
    targets = [(name, PALETTE[name]) for name in ramp]
    if len(targets) > MAX_COLORS:
        raise ValueError("ramp for %r has %d colours (max %d)" % (ramp, len(targets), MAX_COLORS))
    cache = {}
    w, h = art.w, art.h
    for y in range(h):
        for x in range(w):
            r, g, b, a = art.s.get_at((x, y))
            if a < 128:
                art.s.set_at((x, y), (0, 0, 0, 0))
                continue
            key = (r, g, b)
            got = cache.get(key)
            if got is None:
                best = None
                best_d = 1 << 30
                for _name, c in targets:
                    dr, dg, db = r - c[0], g - c[1], b - c[2]
                    d = 2 * dr * dr + 4 * dg * dg + 3 * db * db
                    if d < best_d:
                        best_d = d
                        best = c
                got = best
                cache[key] = got
            art.s.set_at((x, y), (*got, 255))


def colors(art):
    found = Counter()
    for y in range(art.h):
        for x in range(art.w):
            r, g, b, a = art.s.get_at((x, y))
            if a > 127:
                found[(r, g, b)] += 1
    return found


def finish(art, ramp, outline="ink", keep_bottom=False):
    """Outline, quantize, then verify the 12-colour / palette contract."""
    if outline:
        outline_out(art, PALETTE[outline])
    quantize(art, ramp)
    found = colors(art)
    if len(found) > MAX_COLORS:
        raise ValueError("%d colours after quantize" % len(found))
    for rgb in found:
        if rgb not in _PALETTE_SET:
            raise ValueError("colour %r is not in palette.json" % (rgb,))
    return art


_PALETTE_SET = set(PALETTE.values())


def stats(art):
    """Cheap self-check numbers: coverage, colours, edge energy, luminance."""
    w, h = art.w, art.h
    lum = []
    opaque = 0
    for y in range(h):
        row = []
        for x in range(w):
            r, g, b, a = art.s.get_at((x, y))
            if a > 127:
                opaque += 1
            row.append(0.299 * r + 0.587 * g + 0.114 * b)
        lum.append(row)
    edge = 0.0
    edge_n = 0
    for y in range(h):
        for x in range(w - 1):
            edge += abs(lum[y][x] - lum[y][x + 1])
            edge_n += 1
    for y in range(h - 1):
        for x in range(w):
            edge += abs(lum[y][x] - lum[y + 1][x])
            edge_n += 1
    mean_lum = sum(sum(r) for r in lum) / max(1, w * h)
    return {
        "size": (w, h),
        "colours": len(colors(art)),
        "coverage": round(opaque / (w * h), 3),
        "edge": round(edge / max(1, edge_n), 2),
        "lum": round(mean_lum, 1),
    }


def save(art, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(art.s, path)
