"""Station sprites, drawn at the exact size the game needs.

Sizes are locked to data/stations.json heights (48..76 world px); the canvas is
64 wide and every sprite stands on its bottom row (y = h-1).  The renderer
draws the drop shadow, so nothing here paints one.

Shell language (soft industrial, no more "vending machine"):
  * body corners chamfered 1-2 px, counter-top ends cut at 45 degrees;
  * a three-band vertical falloff on the casing - lit top, base middle, bottom
    in shade - instead of one flat fill;
  * a recessed toe kick 5 px tall with rounded corners, inset from the sides;
  * no all-around ink outline: the silhouette is finished with a 1 px lift on
    the left/top rim and 2 px of shade on the right/bottom (see rim_light);
  * metal is one 1 px top rim, never a white slab;
  * knobs, handles and bars get elliptical end caps.

Props still sit ON the top face (baskets, sacks, pan, cleaver, bowl, window,
lid) because that is what tells the stations apart.
"""
from __future__ import annotations

import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from tools.pixel.pxlib import Art, PALETTE, col, dk, h2, li, mix, save, stats

W = 64
HEIGHTS = {
    "station_crate": 54,
    "station_steamer": 72,
    "station_wok": 62,
    "station_oven": 76,
    "station_board": 50,
    "station_assemble": 54,
    "station_serve": 56,
    "station_trash": 48,
}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "assets", "art")

INK = col("ink")
SLATE = col("slate")
STEEL = col("steel")
FOG = col("fog")
SILVER = col("silver")
STEEL_L = col("steel_light")
WHITE = col("white")
CREAM = col("cream")
SAND = col("sand")
IVORY = col("ivory")
LEATHER = col("leather")
COCOA = col("cocoa")
WOOD = col("wood")
CLAY = col("clay")
FLAME = col("flame")
FLAME_L = col("flame_light")
FLAME_D = col("flame_deep")
GLOW = col("glow")
CYAN = col("cyan")
TEAL = col("teal")
LEAF = col("leaf")
LIME = col("lime")
TOMATO = col("tomato")
AMBER = col("amber")
MIST = col("mist")
STEAMC = col("steam")
PLUM = col("plum")
YOLK = col("yolk")

# Cool enamel casing: mix() at 0.62 lands on "fog"; the band tones are pushed
# (see resolve) so they snap to silver above and steel below instead of
# collapsing back onto fog.
METAL = mix(SILVER, FOG, 0.62)
# The toe kick has to sit *under* the casing: slate reads darker than the steel
# the body band snaps to, which is what stops the machine floating.
KICK = dk(SLATE, 0.46)


# --------------------------------------------------------------- palette glue
_PAL = sorted(set(PALETTE.values()))


def snap(c):
    best, bd = None, 1 << 30
    for p in _PAL:
        d = (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2
        if d < bd:
            best, bd = p, d
    return best


def resolve(base, k):
    """Lift (k>0) or drop (k<0) a tone by k light units, far enough to read.

    finish_soft snaps every pixel onto the 32-colour palette.  A literal 20%
    mix of a mid grey snaps straight back onto the same entry, so the band
    would vanish; we keep the requested direction and keep pushing the mix
    until the snapped colour actually changes.  The result is still an
    ordinary colour - finish_soft is what puts it on the palette.
    """
    target = WHITE if k > 0 else INK
    t = min(0.90, abs(k))
    c = mix(base, target, t)
    base_snap = snap(base)
    for _ in range(6):
        if snap(c) != base_snap:
            break
        t = min(0.92, t * 1.45)
        c = mix(base, target, t)
    return c


def _row_spans(x, y, w, h, ctl=0, ctr=0, cbl=0, cbr=0):
    """Row spans of a rectangle with 45-degree corner chamfers."""
    spans = []
    for j in range(h):
        l = r = 0
        if j < ctl:
            l = ctl - j
        if j < ctr:
            r = ctr - j
        bj = h - 1 - j
        if bj < cbl:
            l = max(l, cbl - bj)
        if bj < cbr:
            r = max(r, cbr - bj)
        spans.append((y + j, x + l, x + w - 1 - r))
    return spans


def top_arc(a, x, y, w, h, c, span=0.86):
    """One-pixel lit arc over the upper half of an ellipse (rim light)."""
    cx = x + w / 2.0
    cy = y + h / 2.0
    rx = w / 2.0 - 0.5
    ry = h / 2.0 - 0.5
    for xx in range(int(x), int(x + w)):
        t = (xx - cx) / rx
        if abs(t) > span:
            continue
        yy = int(round(cy - ry * math.sqrt(max(0.0, 1.0 - t * t))))
        a.px(xx, yy, c)


# ------------------------------------------------------------------ the shell
def shell(a, x, y, w, h, base, ctl=2, ctr=2, cbl=1, cbr=1,
          hi=0.20, lo=0.18, hi_frac=0.30, lo_frac=0.32):
    """Casing: chamfered corners plus the three-band vertical falloff."""
    c_hi = resolve(base, +hi)
    c_lo = resolve(base, -lo)
    spans = _row_spans(x, y, w, h, ctl, ctr, cbl, cbr)
    n = len(spans)
    j1 = max(1, int(round(n * hi_frac)))
    j2 = min(n - 1, int(round(n * (1.0 - lo_frac))))
    for j, (yy, x0, x1) in enumerate(spans):
        if j < j1:
            c = c_hi
        elif j > j2:
            c = c_lo
        elif j == j1:
            c = mix(c_hi, base, 0.55)
        elif j == j2:
            c = mix(base, c_lo, 0.55)
        else:
            c = base
        a.hline(x0, x1, yy, c)
    return c_hi, c_lo


def slab(a, x, y, w, depth, shoulder=3, face=None):
    """Counter top: 45-degree rounded ends, ONE lit rim, shaded front lip.

    Rows: lit rim (1 px) / work surface / lip / 1 px shadow line.  That keeps
    the top reading as a surface instead of a white marshmallow cap.
    """
    face = face or SILVER
    rim = resolve(face, +0.40)
    lip = resolve(face, -0.28)
    spans = _row_spans(x, y, w, depth, ctl=shoulder, ctr=shoulder)
    for j, (yy, x0, x1) in enumerate(spans):
        if j == 0:
            c = rim
        elif j == depth - 1:
            c = lip if snap(lip) != snap(face) else FOG
        elif j == depth - 2:
            c = lip
        else:
            c = face
        a.hline(x0, x1, yy, c)
    a.hline(x + shoulder + 1, x + w - shoulder - 2, y + depth - 1, STEEL)
    return


def kick(a, x, y_bottom, w, hgt=5, inset=4, tone=None):
    """Recessed toe kick: 5 px, rounded corners, inset from both sides."""
    tone = tone or KICK
    a.rrect(x + inset, y_bottom - hgt, w - inset * 2, hgt, tone, 2)
    a.hline(x + inset + 2, x + w - inset - 3, y_bottom - hgt, dk(tone, 0.40))


def panel(a, x, y, w, h, glow=None, r=2):
    a.rrect(x, y, w, h, dk(SLATE, 0.58), r)
    a.hline(x + r, x + w - 1 - r, y, dk(SLATE, 0.74))
    a.hline(x + r, x + w - 1 - r, y + h - 1, li(SLATE, 0.20))
    if glow:
        a.hline(x + 3, x + w - 5, y + 2, glow)
        a.hline(x + 3, x + w - 7, y + 3, mix(glow, dk(SLATE, 0.58), 0.45))


def knob(a, x, y, c, w=6, h=5):
    """Elliptical knob: dark bezel, coloured face, one highlight pixel."""
    a.ellipse(x, y, w, h, dk(SLATE, 0.50))
    a.ellipse(x + 1, y + 1, w - 2, h - 2, c)
    a.px(x + 1, y + 1, li(c, 0.42))
    a.px(x + w - 2, y + h - 2, dk(c, 0.38))


def bar(a, x, y, w, h, base, cap=None):
    """Horizontal bar with elliptical end caps (handles, rails, pipes)."""
    cap = max(2, cap or h)
    a.ellipse(x, y, cap, h, base)
    a.ellipse(x + w - cap, y, cap, h, base)
    a.rect(x + cap // 2, y, max(1, w - cap), h, base)
    a.hline(x + cap // 2, x + w - 1 - cap // 2, y, li(base, 0.26))
    a.hline(x + cap // 2, x + w - 1 - cap // 2, y + h - 1, dk(base, 0.34))


def screen(a, x, y, w, h, r=2):
    a.rrect(x, y, w, h, dk(SLATE, 0.40), r)
    a.rrect(x + 1, y + 1, w - 2, h - 2, mix(TEAL, SLATE, 0.50), max(1, r - 1))
    for i in range(3):
        yy = y + 3 + i * 2
        if yy > y + h - 3:
            break
        a.hline(x + 3, x + w - 4 - i * 2, yy, GLOW if i % 2 == 0 else CYAN)


def sack(a, x, y, w, h, base=None, tie=None, mark=None):
    """Tied flour sack: slumped body, pinched neck, coloured tie, stencil.

    A plate has a flat rim and a round body; a sack tapers to a knot, so the
    taper + the saturated tie band are what keep these off the plate shelf.
    """
    base = base or mix(CREAM, SAND, 0.35)
    tie = tie or TEAL
    mark = mark or TOMATO
    cx = x + w // 2
    # body: tapered 45-degree shoulders, flat bottom, lit left / shaded right
    spans = _row_spans(x + 1, y + 7, w - 2, h - 7, ctl=3, ctr=3, cbl=1, cbr=1)
    n = len(spans)
    for j, (yy, x0, x1) in enumerate(spans):
        if j < 2:
            c = li(base, 0.12)
        elif j > n - 3:
            c = dk(base, 0.16)
        else:
            c = base
        a.hline(x0, x1, yy, c)
        if x1 - x0 > 8:
            a.hline(x1 - max(3, (x1 - x0) // 3), x1, yy, dk(base, 0.15))
    # gathered neck: narrower than the body, with two fabric ears
    a.rect(cx - 4, y + 4, 8, 4, base)
    a.hline(cx - 4, cx + 3, y + 3, li(base, 0.34))
    a.rect(cx - 6, y + 6, 2, 2, mix(base, dk(base, 0.20), 0.50))
    a.rect(cx + 5, y + 6, 2, 2, mix(base, dk(base, 0.20), 0.50))
    # tie band - the one saturated accent
    a.rect(cx - 4, y + 8, 9, 3, tie)
    a.hline(cx - 4, cx + 3, y + 8, li(tie, 0.38))
    a.hline(cx - 3, cx + 3, y + 10, dk(tie, 0.22))
    a.rect(cx + 5, y + 9, 2, 3, dk(tie, 0.30))
    # stencil label on the belly
    a.rect(x + 3, y + h - 11, 9, 5, mix(base, WHITE, 0.20))
    a.hline(x + 4, x + 10, y + h - 9, mark)
    a.hline(x + 4, x + 8, y + h - 8, mark)

def egg_tray(a, x, y, w, h):
    """A cardboard egg flat with visible cups - dark tray so the eggs read."""
    tray = mix(LEATHER, CLAY, 0.55)
    a.rrect(x, y, w, h, tray, 2)
    a.hline(x + 2, x + w - 3, y, li(tray, 0.24))
    a.hline(x + 2, x + w - 3, y + h - 1, dk(tray, 0.35))
    for cx in (x + 2, x + 9, x + 16):
        for cy in (y + 2, y + 7):
            a.ellipse(cx, cy, 6, 4, dk(tray, 0.34))
            a.ellipse(cx + 1, cy, 4, 3, mix(CREAM, SAND, 0.25))
            a.px(cx + 2, cy, YOLK)


def basket(a, x, y, ww, bh, bamboo, rim, dark):
    """Bamboo steamer: chamfered drum, lit rim, horizontal slats, binding."""
    spans = _row_spans(x, y, ww, bh, ctl=2, ctr=2, cbl=2, cbr=2)
    for j, (yy, x0, x1) in enumerate(spans):
        if j < 2:
            c = rim
        elif j == 2:
            c = mix(rim, bamboo, 0.55)
        elif j >= bh - 2:
            c = dark
        else:
            c = bamboo
        a.hline(x0, x1, yy, c)
    for j in range(4, bh - 3):
        if (j - 4) % 3 == 0:
            yy, x0, x1 = spans[j]
            a.hline(x0 + 1, x1 - 1, yy, mix(bamboo, COCOA, 0.38))
    for j, (yy, x0, x1) in enumerate(spans):
        a.px(x0, yy, mix(bamboo, COCOA, 0.50))
        a.px(x1, yy, dk(bamboo, 0.42))
    yy, x0, x1 = spans[0]
    a.hline(x0 + 3, x1 - 3, yy, li(rim, 0.30))


# --------------------------------------------------------------- finish pass
def rim_light(a, lit=0.17, dark=0.26, dark2=0.12):
    """Finish the silhouette without an all-around ink line.

    One pixel is lifted on the left/top rim and two pixels are dropped on the
    right/bottom (a hard edge plus a softer second row).  Interior pockets -
    the toe-kick recess, panel edges - get the same treatment, and that is what
    makes a chamfer read as a rounded shoulder instead of a cut corner.
    """
    s = a.s
    grid = [[None] * a.w for _ in range(a.h)]
    for y in range(a.h):
        for x in range(a.w):
            c = s.get_at((x, y))
            if c.a >= 128:
                grid[y][x] = (c.r, c.g, c.b)

    def solid(x, y):
        return 0 <= x < a.w and 0 <= y < a.h and grid[y][x] is not None

    out = [row[:] for row in grid]
    for y in range(a.h):
        for x in range(a.w):
            c = grid[y][x]
            if c is None:
                continue
            if (not solid(x - 1, y) or not solid(x, y - 1)) and y < a.h - 3:
                out[y][x] = li(c, lit)
            elif not solid(x + 1, y) or not solid(x, y + 1):
                out[y][x] = dk(c, dark)
            elif not solid(x + 2, y) or not solid(x, y + 2):
                out[y][x] = dk(c, dark2)
    for y in range(a.h):
        for x in range(a.w):
            c = out[y][x]
            if c is not None:
                s.set_at((x, y), (int(c[0]), int(c[1]), int(c[2]), 255))


def finish_soft(a, limit=20, foot=2):
    """Soft finish: rim light, firm ground contact, then palette snap.

    No drop shadow (the renderer paints that), but a 2 px near-ink contact line
    along the very bottom row so the device sits on the floor at 2x.
    """
    rim_light(a)
    if foot >= 1:
        for x in range(a.w):
            if a.s.get_at((x, a.h - 1)).a >= 128:
                a.px(x, a.h - 1, INK)
            if foot >= 2 and a.s.get_at((x, a.h - 2)).a >= 128:
                a.px(x, a.h - 2, SLATE)
    used = {}
    for y in range(a.h):
        for x in range(a.w):
            c = a.s.get_at((x, y))
            if c.a < 128:
                continue
            k = (c.r, c.g, c.b)
            if k not in used:
                used[k] = snap(k)
            p = used[k]
            a.s.set_at((x, y), (p[0], p[1], p[2], 255))
    # Fold strays: rim-lighting one-pixel accents can produce a colour used by
    # two or three pixels only.  When that pushes us over the cap, the smallest
    # colour is folded into its nearest neighbour already on the image - still
    # a palette colour, and nothing visible at 2x is lost.
    counts = Counter()
    for y in range(a.h):
        for x in range(a.w):
            c = a.s.get_at((x, y))
            if c.a >= 128:
                counts[(c.r, c.g, c.b)] += 1
    while len(counts) > limit:
        victim = min(counts, key=lambda k: counts[k])
        near = min((k for k in counts if k != victim),
                   key=lambda k: sum((k[i] - victim[i]) ** 2 for i in range(3)))
        for y in range(a.h):
            for x in range(a.w):
                c = a.s.get_at((x, y))
                if c.a >= 128 and (c.r, c.g, c.b) == victim:
                    a.px(x, y, near)
        counts[near] += counts.pop(victim)
    n = len(counts)
    assert n <= limit, (n, sorted(counts))
    a.n_colors = n
    return n


# ------------------------------------------------------------------ stations
def crate():
    """木箱：敞口木箱，顶上两只面袋与一格鸡蛋托盘。"""
    a = Art(W, HEIGHTS["station_crate"])
    h = a.h
    wood = mix(WOOD, CLAY, 0.30)
    rail = 20
    # crate body: chamfered, planked, three-band falloff
    shell(a, 2, rail, 60, h - rail - 1, wood, ctl=2, ctr=2, cbl=1, cbr=1,
          hi=0.20, lo=0.18, hi_frac=0.16, lo_frac=0.30)
    for x in range(8, 58, 11):
        a.vline(x, rail + 1, h - 4, dk(wood, 0.36))
        a.vline(x + 1, rail + 1, h - 4, li(wood, 0.12))
    # contents above the rim (rim is painted afterwards so they tuck behind it)
    sack(a, 2, 2, 20, 16)
    sack(a, 45, 3, 17, 15, base=mix(CREAM, SAND, 0.55))
    egg_tray(a, 23, 5, 21, 12)
    # opening rim: one lit edge, 45-degree shoulders
    slab(a, 1, rail - 5, 62, 6, shoulder=2, face=mix(CREAM, SAND, 0.35))
    # shipping label: cream plate, red stencil block, two short rules
    a.rrect(23, h - 22, 18, 10, mix(CREAM, SAND, 0.20), 2)
    a.hline(25, 38, h - 22, li(CREAM, 0.30))
    a.rect(26, h - 19, 5, 4, TOMATO)
    a.hline(33, 38, h - 18, dk(COCOA, 0.30))
    a.hline(33, 36, h - 16, dk(COCOA, 0.30))
    a.hline(26, 38, h - 14, mix(COCOA, SAND, 0.45))
    # corner straps: flat steel plate with two bolts (no hourglass)
    for bx in (3, 55):
        a.rect(bx, rail + 3, 4, 9, mix(STEEL, FOG, 0.30))
        a.hline(bx, bx + 3, rail + 3, li(STEEL, 0.35))
        a.hline(bx, bx + 3, rail + 11, dk(STEEL, 0.40))
        a.px(bx + 1, rail + 5, dk(STEEL, 0.50))
        a.px(bx + 1, rail + 9, dk(STEEL, 0.50))
    kick(a, 2, h, 60, hgt=4, inset=4, tone=dk(wood, 0.55))
    finish_soft(a)
    return a


def steamer():
    """蒸笼：两层竹蒸屉架在矮柜上，蒸汽绕过屉顶。"""
    a = Art(W, HEIGHTS["station_steamer"])
    base_h = 44
    shell(a, 1, base_h, 62, a.h - base_h, METAL, ctl=2, ctr=2)
    kick(a, 1, a.h, 62, hgt=5, inset=4)
    slab(a, 1, base_h - 7, 62, 7, shoulder=3)
    a.hline(3, 60, base_h + 1, TEAL)
    a.hline(3, 60, base_h + 2, dk(TEAL, 0.35))
    panel(a, 7, base_h + 7, 23, 10, glow=GLOW)
    knob(a, 36, base_h + 9, TEAL)
    knob(a, 45, base_h + 8, AMBER)
    # ---- two bamboo baskets + lid
    bamboo = mix(LEATHER, SAND, 0.62)
    rim = mix(bamboo, CREAM, 0.55)
    dark = dk(bamboo, 0.46)
    lower = (base_h - 7 - 16, 50, 16)
    upper = (base_h - 7 - 31, 46, 15)
    for y, ww, bh in (lower, upper):
        x = (W - ww) // 2
        basket(a, x, y, ww, bh, bamboo, rim, dark)
        for hx in (x - 3, x + ww - 1):
            a.ellipse(hx, y + 3, 4, 5, mix(bamboo, COCOA, 0.30))
            a.px(hx + 1, y + 4, rim)
    a.hline((W - 46) // 2 + 1, (W + 46) // 2 - 2, lower[0] - 1, dk(bamboo, 0.55))
    # lid
    ly = upper[0] - 7
    a.rrect(10, ly, 44, 7, mix(bamboo, CREAM, 0.35), 2)
    a.hline(13, 50, ly, rim)
    a.hline(13, 50, ly + 6, dark)
    a.hline(13, 50, ly + 3, mix(bamboo, COCOA, 0.30))
    bar(a, 27, ly - 4, 10, 4, mix(bamboo, COCOA, 0.40), cap=4)
    # soft steam (a touch of grey so it reads on a pale floor)
    wisp = mix(STEAMC, FOG, 0.45)
    a.steam(12, ly + 2, 11, MIST, wisp, seed=1, width=2)
    a.steam(31, ly - 2, 9, MIST, wisp, seed=4, width=2)
    a.steam(49, ly + 1, 12, MIST, wisp, seed=2, width=2)
    a.steam(21, ly - 3, 6, MIST, wisp, seed=6, width=1)
    a.steam(41, ly - 4, 5, MIST, wisp, seed=8, width=1)
    finish_soft(a)
    return a


def wok():
    """灶台：黑铁炒锅架在火圈上，锅沿一道冷光。"""
    a = Art(W, HEIGHTS["station_wok"])
    base_h = 36
    shell(a, 1, base_h, 62, a.h - base_h, METAL, ctl=2, ctr=2)
    kick(a, 1, a.h, 62, hgt=5, inset=4)
    slab(a, 1, base_h - 7, 62, 7, shoulder=3)
    a.hline(3, 60, base_h + 1, FLAME)
    a.hline(3, 60, base_h + 2, dk(FLAME, 0.35))
    panel(a, 7, base_h + 8, 21, 10, glow=AMBER)
    knob(a, 34, base_h + 9, FLAME)
    knob(a, 43, base_h + 8, TEAL)
    # burner ring + flame licks (painted first, the pan occludes the middle)
    a.ellipse(9, base_h - 13, 46, 11, dk(SLATE, 0.55))
    a.hline(14, 49, base_h - 13, dk(SLATE, 0.30))
    for x in range(12, 53, 3):
        a.vline(x, base_h - 12, base_h - 8, dk(SLATE, 0.78))
    for i, x in enumerate(range(11, 54, 4)):
        hh = 3 + (i * 7) % 4
        a.vline(x, base_h - 13 - hh, base_h - 12, FLAME)
        a.px(x, base_h - 14 - hh, FLAME_L)
        a.hline(x - 1, x + 1, base_h - 13, dk(FLAME_D, 0.15))
    # pan
    a.ellipse(3, 4, 58, 24, dk(SLATE, 0.72))
    a.ellipse(4, 5, 56, 22, dk(SLATE, 0.52))
    a.ellipse(6, 7, 52, 19, dk(SLATE, 0.32))
    a.ellipse(9, 10, 46, 15, mix(FLAME_D, COCOA, 0.50))
    a.ellipse(11, 12, 42, 12, mix(FLAME_D, AMBER, 0.32))
    a.ellipse(14, 14, 36, 9, mix(FLAME_D, FLAME, 0.45))
    top_arc(a, 4, 5, 56, 22, li(SLATE, 0.42), span=0.92)
    # food + flame licks in the wok
    for i, x in enumerate((17, 24, 31, 38, 45)):
        a.ellipse(x, 18 + (i % 2), 5, 3, CREAM if i % 2 else SAND)
    for i, x in enumerate((20, 28, 36, 44)):
        hh = 3 + (i % 2) * 2
        a.vline(x, 17 - hh, 19, FLAME)
        a.px(x, 16 - hh, FLAME_L)
    a.px(33, 16, AMBER)
    a.hline(16, 48, 21, dk(FLAME_D, 0.20))
    # pan handles with elliptical caps
    bar(a, 0, 10, 8, 4, mix(STEEL, FOG, 0.30), cap=4)
    bar(a, 56, 10, 8, 4, mix(STEEL, FOG, 0.30), cap=4)
    a.px(2, 11, FOG)
    a.px(61, 11, FOG)
    finish_soft(a)
    return a


def oven():
    """烤炉：立式炉柜，橙色炉门透火光，横把手两端椭圆收头。"""
    a = Art(W, HEIGHTS["station_oven"])
    h = a.h
    shell(a, 2, 10, 60, h - 10, METAL, ctl=2, ctr=2, cbl=1, cbr=1, hi_frac=0.24)
    kick(a, 2, h, 60, hgt=5, inset=4)
    slab(a, 2, 0, 60, 10, shoulder=3)
    a.hline(4, 59, 10, AMBER)
    a.hline(4, 59, 11, dk(AMBER, 0.32))
    panel(a, 6, 15, 52, 12, glow=GLOW)
    for x, c in ((9, TEAL), (18, CYAN), (27, AMBER)):
        knob(a, x, 18, c)
    a.rect(38, 19, 17, 4, dk(SLATE, 0.25))
    a.hline(40, 52, 20, GLOW)
    # oven door: rounded, warm three-tone glow, one lit rim
    dy, dh = 32, h - 32 - 12
    a.rrect(6, dy, 52, dh, dk(SLATE, 0.62), 3)
    a.rrect(8, dy + 2, 48, dh - 4, FLAME_D, 2)
    a.rrect(10, dy + 4, 44, dh - 8, mix(FLAME_D, FLAME, 0.45), 2)
    a.rrect(12, dy + 8, 40, dh - 14, FLAME, 2)
    a.hline(14, 50, dy + 9, FLAME_L)
    a.hline(14, 50, dy + 10, mix(FLAME_L, FLAME, 0.55))
    for x in range(16, 52, 6):
        a.vline(x, dy + 11, dy + dh - 8, dk(COCOA, 0.20))
    a.hline(10, 53, dy + 3, mix(FLAME_L, FLAME, 0.60))
    a.hline(10, 53, dy + dh - 5, dk(FLAME_D, 0.32))
    bar(a, 17, dy + 3, 30, 4, mix(STEEL, FOG, 0.25), cap=4)
    a.px(8, h - 14, AMBER)
    finish_soft(a)
    return a


def board():
    """切台：厚木砧板（横木纹 + 前侧厚度带），一把主厨刀横放，两点碎料。"""
    a = Art(W, HEIGHTS["station_board"])
    base_h = 27
    shell(a, 1, base_h, 62, a.h - base_h, METAL, ctl=2, ctr=2)
    kick(a, 1, a.h, 62, hgt=5, inset=4)
    slab(a, 1, base_h - 7, 62, 7, shoulder=3)
    a.hline(3, 60, base_h + 1, LIME)
    a.hline(3, 60, base_h + 2, dk(LIME, 0.35))
    panel(a, 4, base_h + 8, 18, 9)
    knob(a, 27, base_h + 9, TEAL)
    knob(a, 36, base_h + 8, LIME)
    # ---- chopping block, overhanging the counter by 1 px each side.
    # Tones come from the palette's own browns (clay / wood / cocoa): mixing a
    # mid brown toward ink desaturates it until the nearest palette entry is a
    # blue-grey, which made the whole board read as sheet metal.
    top_y, top_h = 1, 13
    edge_y, edge_h = 14, 6
    spans = _row_spans(0, top_y, W, top_h, ctl=2, ctr=2)
    for j, (yy, x0, x1) in enumerate(spans):
        c = CLAY if j < 2 else (WOOD if j > top_h - 3 else CLAY)
        a.hline(x0, x1, yy, c)
    for yy in (5, 8, 11):
        a.hline(3, W - 4, yy, WOOD)
    a.hline(3, 60, top_y, mix(CLAY, SAND, 0.35))
    # front thickness band: cocoa face, end-grain stripes, 45-degree corners
    spans = _row_spans(0, edge_y, W, edge_h, ctl=0, ctr=0, cbl=3, cbr=3)
    for j, (yy, x0, x1) in enumerate(spans):
        a.hline(x0, x1, yy, COCOA if j < 2 else mix(COCOA, LEATHER, 0.55))
    a.hline(0, W - 1, edge_y, WOOD)
    for x in range(4, W - 3, 6):
        a.vline(x, edge_y + 1, edge_y + 4, LEATHER)
    a.hline(0, W - 1, edge_y + edge_h - 1, LEATHER)
    # ---- ONE chef knife: handle left, steel blade tapering to the right
    blade = mix(FOG, STEEL, 0.30)
    a.rrect(1, 4, 14, 6, COCOA, 2)
    a.hline(3, 13, 4, mix(COCOA, SAND, 0.42))
    a.hline(3, 13, 9, dk(COCOA, 0.40))
    a.px(5, 6, STEEL)
    a.px(11, 6, STEEL)
    a.rect(16, 3, 3, 8, STEEL)
    a.hline(16, 18, 3, STEEL_L)
    a.poly([(19, 3), (47, 3), (52, 5), (52, 8), (19, 8)], blade)
    a.hline(20, 47, 3, STEEL)
    a.hline(20, 48, 4, mix(blade, WHITE, 0.34))
    a.hline(19, 50, 8, WHITE)
    a.vline(51, 5, 7, mix(blade, WHITE, 0.55))
    # ---- two chopped-veg dots only: the knife owns the silhouette
    for x, y, c in ((24, 10, TOMATO), (32, 10, LEAF)):
        a.rect(x, y, 3, 3, c)
        a.px(x, y, li(c, 0.35))
    finish_soft(a)
    return a


def assemble():
    """组装台：深盆朝前倾斜，锅铲斜插，左前一只配料浅盘，青色屏在右前。"""
    a = Art(W, HEIGHTS["station_assemble"])
    base_h = 34
    shell(a, 1, base_h, 62, a.h - base_h, METAL, ctl=2, ctr=2)
    kick(a, 1, a.h, 62, hgt=5, inset=4)
    slab(a, 1, base_h - 7, 62, 7, shoulder=3)
    a.hline(3, 60, base_h + 1, TEAL)
    a.hline(3, 60, base_h + 2, dk(TEAL, 0.35))
    screen(a, 33, base_h + 5, 25, 12)
    knob(a, 6, base_h + 7, LIME)
    knob(a, 14, base_h + 7, AMBER)
    # ---- deep mixing bowl tipped toward the player
    a.ellipse(11, 5, 42, 23, dk(SLATE, 0.58))          # outer wall in shade
    a.ellipse(12, 6, 40, 21, mix(STEEL, FOG, 0.55))    # steel shell
    a.ellipse(13, 3, 38, 15, dk(SLATE, 0.66))          # mouth aperture
    a.ellipse(14, 4, 36, 13, mix(STEEL, FOG, 0.10))    # inner wall (kept dark)
    a.ellipse(16, 6, 32, 10, dk(SLATE, 0.42))          # depth
    a.ellipse(18, 8, 28, 7, mix(CREAM, SAND, 0.35))    # batter
    a.ellipse(22, 9, 6, 4, TOMATO)
    a.ellipse(31, 8, 7, 4, LEAF)
    a.px(27, 10, YOLK)
    a.hline(14, 48, 3, STEEL_L)                        # ONE 1 px metal rim
    top_arc(a, 13, 3, 38, 15, li(STEEL_L, 0.20), span=0.80)
    # ---- spatula leaning out of the bowl
    for i in range(10):
        a.rect(40 + int(i * 1.6), 10 - i, 3, 1, mix(COCOA, SAND, 0.35))
    a.px(40, 10, dk(COCOA, 0.35))
    a.rrect(53, 0, 8, 5, STEEL_L, 2)
    a.hline(54, 58, 1, li(STEEL_L, 0.32))
    a.vline(57, 1, 3, dk(STEEL_L, 0.25))
    # ---- ingredient tray, front left (drawn last = nearest)
    tray = mix(CLAY, COCOA, 0.30)
    a.rrect(0, 21, 19, 7, dk(SLATE, 0.50), 2)
    a.rrect(1, 20, 17, 7, tray, 2)
    a.hline(3, 15, 20, li(tray, 0.34))
    a.hline(3, 15, 25, dk(tray, 0.42))
    a.vline(1, 22, 24, li(tray, 0.18))
    for cx, c in ((4, TOMATO), (9, LEAF), (14, SAND)):
        a.ellipse(cx, 22, 4, 4, c)
        a.px(cx + 1, 22, li(c, 0.35))
    finish_soft(a)
    return a


def serve():
    """出餐口：窗口透出暖光，盘子在台口上。"""
    a = Art(W, HEIGHTS["station_serve"])
    h = a.h
    shell(a, 2, 8, 60, h - 8, METAL, ctl=2, ctr=2, cbl=1, cbr=1, hi_frac=0.20)
    kick(a, 2, h, 60, hgt=5, inset=4)
    slab(a, 2, 0, 60, 8, shoulder=3)
    # warm window: rounded opening, three light bands, 1 px lit rim
    a.rrect(6, 9, 52, 31, dk(SLATE, 0.62), 3)
    a.rrect(8, 11, 48, 27, mix(FLAME_D, COCOA, 0.35), 2)
    a.hline(11, 52, 12, FLAME_L)
    a.hline(11, 52, 13, mix(FLAME_L, AMBER, 0.35))
    a.hline(11, 52, 14, AMBER)
    a.hline(11, 52, 20, mix(FLAME, AMBER, 0.40))
    a.hline(11, 52, 26, mix(FLAME, FLAME_D, 0.45))
    a.rrect(9, 27, 46, 11, mix(FLAME_D, AMBER, 0.30), 2)
    a.hline(11, 52, 37, dk(FLAME_D, 0.35))
    a.vline(9, 13, 36, dk(FLAME_D, 0.30))
    a.vline(54, 13, 36, dk(FLAME_D, 0.30))
    # plate with a rim, food in the middle
    a.ellipse(17, 22, 30, 12, CREAM)
    a.ellipse(19, 23, 26, 9, IVORY)
    a.ellipse(22, 24, 20, 7, mix(IVORY, SAND, 0.45))
    a.ellipse(24, 25, 11, 4, SAND)
    a.px(29, 26, TOMATO)
    a.px(33, 27, LEAF)
    a.px(27, 27, YOLK)
    # counter lip with elliptical ends + ticket light
    bar(a, 3, 41, 58, 5, mix(SILVER, SAND, 0.35), cap=5)
    a.rrect(29, 47, 8, 3, AMBER, 1)
    a.px(32, 47, GLOW)
    finish_soft(a)
    return a


def trash():
    """垃圾桶：深色桶身配危险条纹，盖子下面露出袋口。"""
    a = Art(W, HEIGHTS["station_trash"])
    h = a.h
    shell(a, 4, 9, 56, h - 9, dk(SLATE, 0.25), ctl=2, ctr=2, cbl=1, cbr=1,
          hi=0.20, lo=0.18, hi_frac=0.26)
    for x in range(11, 56, 7):
        a.vline(x, 12, h - 7, dk(SLATE, 0.45))
        a.vline(x + 1, 12, h - 7, li(SLATE, 0.10))
    # hazard band: 45-degree stripes inside a rounded band
    hazard = mix(AMBER, SAND, 0.25)
    spans = _row_spans(7, 26, 50, 10, ctl=2, ctr=2, cbl=2, cbr=2)
    for j, (yy, x0, x1) in enumerate(spans):
        for xx in range(x0, x1 + 1):
            a.px(xx, yy, hazard if ((xx + yy) // 3) % 2 else dk(COCOA, 0.35))
    a.hline(10, 53, 26, li(hazard, 0.25))
    a.hline(10, 53, 35, dk(COCOA, 0.45))
    # lid: 45-degree shoulders, elliptical handle, bag peeking out
    slab(a, 2, 0, 60, 9, shoulder=3, face=mix(FOG, SILVER, 0.35))
    a.rrect(30, 6, 8, 5, dk(PLUM, 0.35), 1)
    a.hline(31, 36, 6, mix(PLUM, WHITE, 0.25))
    bar(a, 25, 2, 14, 4, dk(STEEL, 0.30), cap=4)
    a.px(7, 10, li(SILVER, 0.25))
    kick(a, 4, h, 56, hgt=4, inset=5)
    finish_soft(a)
    return a


BUILDERS = {
    "station_crate": crate,
    "station_steamer": steamer,
    "station_wok": wok,
    "station_oven": oven,
    "station_board": board,
    "station_assemble": assemble,
    "station_serve": serve,
    "station_trash": trash,
}


def main():
    pygame.init()
    for key, fn in BUILDERS.items():
        art = fn()
        assert art.w == W and art.h == HEIGHTS[key], (key, art.w, art.h)
        save(art, os.path.join(OUT, key + ".png"))
        print(key, art.w, art.h, stats(art))


if __name__ == "__main__":
    main()
