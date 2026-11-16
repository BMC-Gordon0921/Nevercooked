"""Station sprites, drawn at the exact size the game needs.

Sizes are locked to data/stations.json heights (54..76 world px).  The chef is
64 px tall, so a counter reads as waist height and a stove as chest height:
anything taller turns the kitchen into a warehouse of vending machines.

Construction rule: every sprite is a *base* (counter/cabinet standing on the
floor) with props sitting ON its top surface.  So the base's top edge is at y =
base_h, and props are painted in 0..base_h.  Getting this backwards is what
makes a steamer look like a grey fridge with a floating lid.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from tools.pixel.pxlib import (Art, PALETTE, col, dk, h2, li, mix, outline_out,
                               save, stats)

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
STEEL = col("steel")
FOG = col("fog")
SILVER = col("silver")
SLATE = col("slate")
WHITE = col("white")
CREAM = col("cream")
SAND = col("sand")
LEATHER = col("leather")
COCOA = col("cocoa")
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
PLUM = col("plum")
BLUSH = col("blush")

METAL = mix(SILVER, FOG, 0.50)          # light cool enamel
METAL_TOP = mix(SILVER, WHITE, 0.45)    # lit work surface
KICK = dk(SLATE, 0.30)


def finish_soft(a, limit=20):
    """Outline, then snap every tone onto the 32-colour palette.

    Snapping to a hand-written 12-colour ramp wrecks warm materials (tan bamboo
    turns cream, wood turns grey); snapping to the *palette* keeps the hue and
    still ends up with a small, coherent colour count.
    """
    outline_out(a, INK)
    names = sorted(PALETTE)
    pal = [(n, PALETTE[n]) for n in names]
    seen = set()
    for y in range(a.h):
        for x in range(a.w):
            c = a.s.get_at((x, y))
            if c.a < 128:
                continue
            best, bd = None, 1 << 30
            for name, rgb in pal:
                d = ((c.r - rgb[0]) ** 2 + (c.g - rgb[1]) ** 2 + (c.b - rgb[2]) ** 2)
                if d < bd:
                    best, bd = rgb, d
            a.s.set_at((x, y), (*best, 255))
            seen.add(best)
    if len(seen) > limit:
        raise ValueError("%d palette colours (limit %d)" % (len(seen), limit))
    return a


# --------------------------------------------------------------------- shell
def base(a, base_h, accent, kick_h=6, inset=1):
    """Counter/cabinet from y=base_h down to the floor, with an accent band."""
    w = a.w - inset * 2
    a.rect(inset, base_h, w, a.h - base_h, METAL)
    a.rect(inset, base_h, w, max(2, (a.h - base_h) // 5), li(METAL, 0.14))
    a.hline(inset, inset + w - 1, base_h, METAL_TOP)
    a.hline(inset, inset + w - 1, base_h + 1, li(METAL, 0.30))
    a.hline(inset, inset + w - 1, base_h + 2, accent)
    a.hline(inset, inset + w - 1, base_h + 3, dk(accent, 0.25))
    a.rect(inset, a.h - kick_h, w, kick_h, KICK)
    a.hline(inset, inset + w - 1, a.h - kick_h, dk(KICK, 0.25))
    a.vline(inset, base_h, a.h - 1, li(METAL, 0.28))
    a.vline(inset + w - 1, base_h, a.h - 1, dk(METAL, 0.22))
    # seams so a 64px cabinet does not read as one flat slab
    for x in (inset + 12, w - 14):
        a.vline(x, base_h + 6, a.h - kick_h - 3, dk(METAL, 0.10))


def counter_top(a, base_h, depth=8):
    """The lit work surface: a thin slab whose front lip is visible."""
    a.rect(0, base_h - depth, a.w, depth, METAL_TOP)
    a.hline(0, a.w - 1, base_h - depth, WHITE)
    a.hline(0, a.w - 1, base_h - depth + 1, li(METAL_TOP, 0.55))
    a.hline(0, a.w - 1, base_h - 1, FOG)
    a.hline(0, a.w - 1, base_h - 2, dk(METAL_TOP, 0.10))


def panel(a, x, y, w, h, glow=None):
    a.rect(x, y, w, h, dk(SLATE, 0.45))
    a.hline(x, x + w - 1, y, dk(SLATE, 0.60))
    a.hline(x, x + w - 1, y + h - 1, li(SLATE, 0.12))
    if glow:
        a.hline(x + 2, x + w - 3, y + 2, glow)


def knob(a, x, y, c):
    a.rect(x, y, 5, 5, dk(SLATE, 0.35))
    a.rect(x + 1, y + 1, 3, 3, c)
    a.px(x + 1, y + 1, li(c, 0.55))


# ------------------------------------------------------------------ stations
def crate():
    """木箱：敞口木箱，顶上露出米袋、菜叶与番茄。"""
    a = Art(W, HEIGHTS["station_crate"])
    h = a.h
    rail = 15
    wood = mix(LEATHER, SAND, 0.30)
    a.rect(3, rail, W - 6, h - rail - 4, wood)
    for x in range(5, W - 6, 10):
        a.vline(x, rail, h - 6, dk(wood, 0.30))
        a.vline(x + 1, rail, h - 6, li(wood, 0.14))
    a.hline(3, W - 4, h - 5, dk(wood, 0.42))
    # hardware rails
    a.rect(3, rail + 10, W - 6, 3, dk(STEEL, 0.30))
    a.hline(3, W - 4, rail + 10, li(STEEL, 0.10))
    # rim + contents
    a.rect(2, rail - 4, W - 4, 6, mix(CREAM, SAND, 0.35))
    a.hline(2, W - 3, rail - 4, WHITE)
    a.hline(2, W - 3, rail + 1, dk(CREAM, 0.30))
    a.rect(6, 4, W - 12, rail - 6, dk(COCOA, 0.40))
    a.ellipse(7, 0, 16, 10, CREAM)                 # rice sack
    a.rect(9, 5, 12, 6, CREAM)
    a.hline(9, 20, 5, li(CREAM, 0.30))
    a.ellipse(24, 1, 14, 9, LEAF)                  # greens
    a.ellipse(26, 0, 8, 7, LIME)
    a.ellipse(38, 2, 13, 8, TOMATO)                # tomatoes
    a.ellipse(40, 1, 6, 5, li(TOMATO, 0.30))
    a.ellipse(49, 3, 12, 8, SAND)                  # dough
    a.hline(50, 59, 5, li(SAND, 0.30))
    a.rect(23, h - 19, 18, 10, CREAM)              # label
    a.rect(24, h - 18, 16, 8, li(CREAM, 0.15))
    a.hline(26, 37, h - 15, dk(CREAM, 0.55))
    a.hline(26, 34, h - 12, dk(CREAM, 0.30))
    finish_soft(a)
    return a


def steamer():
    """蒸笼：竹蒸屉叠放在矮柜上，屉缝与竹编纹理把圆柱感做出来。"""
    a = Art(W, HEIGHTS["station_steamer"])
    base_h = 40
    base(a, base_h, TEAL)
    counter_top(a, base_h, depth=7)
    panel(a, 8, base_h + 8, 22, 9, glow=GLOW)
    knob(a, 36, base_h + 10, TEAL)
    knob(a, 44, base_h + 10, AMBER)
    bamboo = mix(LEATHER, SAND, 0.52)
    rim = mix(bamboo, CREAM, 0.45)
    dark = dk(bamboo, 0.42)
    for y, ww, bh in ((base_h - 8 - 14, 46, 14), (base_h - 8 - 28, 42, 14)):
        x = (W - ww) // 2
        a.rect(x, y, ww, bh, bamboo)
        a.hline(x, x + ww - 1, y, rim)
        a.hline(x, x + ww - 1, y + 1, rim)
        a.hline(x, x + ww - 1, y + 2, mix(rim, bamboo, 0.55))
        a.hline(x, x + ww - 1, y + bh - 1, dark)
        a.hline(x, x + ww - 1, y + bh - 2, dk(bamboo, 0.22))
        for xx in range(x + 2, x + ww - 2, 4):
            a.vline(xx, y + 3, y + bh - 3, mix(bamboo, COCOA, 0.40))
        a.vline(x, y + 1, y + bh - 1, rim)
        a.vline(x + ww - 1, y + 1, y + bh - 1, dark)
    ly = base_h - 8 - 28 - 7
    a.rect((W - 44) // 2, ly, 44, 7, mix(bamboo, CREAM, 0.25))
    a.hline((W - 44) // 2, (W + 44) // 2 - 1, ly, rim)
    a.hline((W - 44) // 2, (W + 44) // 2 - 1, ly + 6, dark)
    a.rect(26, ly - 4, 12, 4, mix(bamboo, COCOA, 0.30))
    a.hline(26, 37, ly - 4, rim)
    a.steam(14, ly + 2, 10, WHITE, MIST, seed=1, width=2)
    a.steam(48, ly, 12, WHITE, MIST, seed=2, width=2)
    a.hline(11, 52, base_h - 8, FLAME_D)
    a.hline(13, 50, base_h - 7, FLAME)
    finish_soft(a)
    return a


def wok():
    """灶台：黑铁炒锅架在火口上，锅沿与锅底火光把圆度做出来。"""
    a = Art(W, HEIGHTS["station_wok"])
    base_h = 32
    base(a, base_h, FLAME)
    counter_top(a, base_h, depth=7)
    panel(a, 8, base_h + 9, 20, 9, glow=AMBER)
    knob(a, 34, base_h + 11, FLAME)
    knob(a, 42, base_h + 11, TEAL)
    a.rect(10, base_h - 10, 44, 5, dk(SLATE, 0.55))
    a.hline(10, 53, base_h - 10, dk(SLATE, 0.28))
    for x in range(12, 52, 5):
        a.vline(x, base_h - 9, base_h - 6, dk(SLATE, 0.78))
    for x in range(13, 52, 4):
        a.vline(x, base_h - 14, base_h - 11, FLAME)
        a.px(x, base_h - 15, FLAME_L)
    a.ellipse(4, base_h - 28, 56, 24, INK)
    a.ellipse(5, base_h - 27, 54, 22, dk(SLATE, 0.45))
    a.ellipse(7, base_h - 25, 50, 19, dk(SLATE, 0.62))
    a.ellipse(10, base_h - 22, 44, 14, mix(FLAME_D, COCOA, 0.55))
    a.ellipse(13, base_h - 20, 38, 10, mix(FLAME_D, AMBER, 0.30))
    for i, x in enumerate((16, 23, 30, 37, 44)):
        hh = 4 + (i % 2) * 2
        a.vline(x, base_h - 16 - hh, base_h - 14, FLAME)
        a.px(x, base_h - 17 - hh, FLAME_L)
    for i, x in enumerate((20, 27, 34, 41)):
        a.ellipse(x, base_h - 19 + (i % 2), 5, 3, CREAM if i % 2 else SAND)
    a.px(31, base_h - 20, FLAME_L)
    a.hline(14, 49, base_h - 21, dk(FLAME_D, 0.15))
    a.rect(0, base_h - 22, 6, 4, dk(SLATE, 0.25))
    a.rect(58, base_h - 22, 6, 4, dk(SLATE, 0.25))
    a.hline(0, 5, base_h - 22, SILVER)
    a.hline(58, 63, base_h - 22, SILVER)
    finish_soft(a)
    return a


def oven():
    """烤炉：立式炉柜，橙色炉门透火光，门上把手。"""
    a = Art(W, HEIGHTS["station_oven"])
    h = a.h
    top_h = 12
    a.rect(2, top_h, W - 4, h - top_h - 7, METAL)
    a.rect(2, 0, W - 4, top_h, METAL_TOP)
    a.hline(2, W - 3, 0, WHITE)
    a.hline(2, W - 3, top_h - 1, FOG)
    a.hline(2, W - 3, top_h, AMBER)
    a.hline(2, W - 3, top_h + 1, dk(AMBER, 0.30))
    a.rect(2, h - 7, W - 4, 7, KICK)
    a.vline(2, top_h, h - 1, li(METAL, 0.25))
    a.vline(W - 3, top_h, h - 1, dk(METAL, 0.22))
    # control strip
    panel(a, 6, top_h + 5, 52, 10, glow=GLOW)
    for i, x in enumerate((9, 17, 25)):
        knob(a, x, top_h + 7, (TEAL, CYAN, AMBER)[i])
    a.rect(36, top_h + 8, 18, 4, dk(SLATE, 0.20))
    a.hline(38, 51, top_h + 9, GLOW)
    # door
    dy = top_h + 19
    dh = h - dy - 11
    a.rect(6, dy, 52, dh, dk(SLATE, 0.40))
    a.rect(7, dy + 1, 50, dh - 2, FLAME_D)
    a.rect(9, dy + 3, 46, dh - 6, mix(FLAME, FLAME_D, 0.50))
    a.rect(12, dy + 6, 40, dh - 12, FLAME)
    a.hline(12, 51, dy + 6, FLAME_L)
    for x in range(14, 52, 6):
        a.vline(x, dy + 7, dy + dh - 8, mix(FLAME_D, COCOA, 0.35))
    a.hline(9, 54, dy + 3, li(FLAME_D, 0.25))
    a.hline(9, 54, dy + dh - 4, dk(FLAME_D, 0.35))
    # handle
    a.rect(20, dy + 3, 24, 3, dk(STEEL, 0.20))
    a.hline(20, 43, dy + 3, SILVER)
    a.px(11, h - 10, AMBER)
    finish_soft(a)
    return a


def board():
    """切台：矮柜上一块厚木砧板，宽刃菜刀与碎料摊着。"""
    a = Art(W, HEIGHTS["station_board"])
    base_h = 26
    base(a, base_h, LIME)
    counter_top(a, base_h, depth=7)
    panel(a, 8, base_h + 8, 20, 8)
    knob(a, 34, base_h + 9, TEAL)
    plank = mix(LEATHER, SAND, 0.48)
    a.rect(2, 3, W - 4, base_h - 6, plank)
    a.hline(2, W - 3, 3, mix(plank, CREAM, 0.40))
    a.hline(2, W - 3, 4, mix(plank, CREAM, 0.16))
    a.hline(2, W - 3, base_h - 4, dk(plank, 0.45))
    a.hline(2, W - 3, base_h - 3, dk(plank, 0.28))
    for x in range(7, W - 6, 9):
        a.vline(x, 6, base_h - 5, mix(plank, COCOA, 0.28))
    a.rect(10, 8, 4, 9, dk(COCOA, 0.25))
    a.px(10, 9, LEATHER)
    a.rect(14, 6, 30, 4, mix(SILVER, WHITE, 0.45))
    a.rect(14, 10, 30, 6, SILVER)
    a.rect(15, 11, 28, 4, mix(SILVER, WHITE, 0.25))
    a.hline(14, 43, 16, WHITE)
    a.hline(14, 43, 17, FOG)
    a.rect(47, 7, 6, 4, TOMATO)
    a.px(47, 7, li(TOMATO, 0.35))
    a.rect(54, 10, 5, 3, LEAF)
    a.rect(48, 12, 4, 3, SAND)
    a.px(52, 6, MIST)
    finish_soft(a)
    return a


def assemble():
    """组装台：台面一只钢盆，前面一块青色小屏。"""
    a = Art(W, HEIGHTS["station_assemble"])
    base_h = 30
    base(a, base_h, TEAL)
    counter_top(a, base_h, depth=7)
    a.rect(5, base_h + 8, 26, 13, dk(SLATE, 0.40))
    a.rect(6, base_h + 9, 24, 11, mix(TEAL, SLATE, 0.35))
    for i in range(3):
        a.hline(8, 8 + 14 - i * 5, base_h + 11 + i * 3, GLOW if i % 2 == 0 else CYAN)
    knob(a, 37, base_h + 9, LIME)
    knob(a, 45, base_h + 9, AMBER)
    a.ellipse(13, base_h - 24, 34, 22, dk(FOG, 0.35))
    a.ellipse(14, base_h - 23, 32, 20, li(FOG, 0.30))
    a.ellipse(15, base_h - 22, 30, 17, dk(SLATE, 0.20))
    a.ellipse(17, base_h - 20, 26, 13, mix(STEEL, SAND, 0.35))
    a.ellipse(18, base_h - 19, 24, 11, mix(SAND, CREAM, 0.55))
    a.ellipse(20, base_h - 18, 7, 5, TOMATO)
    a.ellipse(29, base_h - 17, 8, 6, LEAF)
    a.ellipse(37, base_h - 16, 5, 4, SAND)
    a.px(26, base_h - 14, AMBER)
    a.px(33, base_h - 13, CREAM)
    a.hline(15, 46, base_h - 12, li(FOG, 0.15))
    a.hline(20, 42, base_h - 21, WHITE)
    finish_soft(a)
    return a


def serve():
    """出餐口：窗口透出暖光，托盘上摆着刚装好的盘子。"""
    a = Art(W, HEIGHTS["station_serve"])
    h = a.h
    wy = 8
    a.rect(2, 0, W - 4, h - 7, METAL)
    a.rect(2, 0, W - 4, 6, METAL_TOP)
    a.hline(2, W - 3, 0, WHITE)
    a.hline(2, W - 3, 5, FOG)
    a.rect(2, h - 7, W - 4, 7, KICK)
    a.vline(2, 0, h - 1, li(METAL, 0.25))
    a.vline(W - 3, 0, h - 1, dk(METAL, 0.22))
    # open window with warm interior
    a.rect(5, wy, 54, h - wy - 14, dk(SLATE, 0.55))
    a.rect(7, wy + 2, 50, h - wy - 18, mix(AMBER, COCOA, 0.50))
    a.rect(8, wy + 3, 48, h - wy - 21, mix(FLAME_D, AMBER, 0.40))
    a.hline(8, 55, wy + 3, mix(FLAME, AMBER, 0.45))
    a.hline(8, 55, h - 20, dk(FLAME_D, 0.30))
    # plate
    a.ellipse(17, h - 30, 30, 11, CREAM)
    a.ellipse(19, h - 29, 26, 8, WHITE)
    a.ellipse(23, h - 27, 12, 5, SAND)
    a.px(29, h - 28, TOMATO)
    a.px(33, h - 27, LEAF)
    # counter lip + ticket light
    a.rect(3, h - 12, 58, 5, mix(SILVER, SAND, 0.45))
    a.hline(3, 60, h - 12, WHITE)
    a.hline(3, 60, h - 8, dk(SILVER, 0.30))
    a.rect(24, h - 6, 16, 3, AMBER)
    a.px(31, h - 6, GLOW)
    finish_soft(a)
    return a


def trash():
    """垃圾桶：深色桶身配危险条纹，盖子下面露出袋口。"""
    a = Art(W, HEIGHTS["station_trash"])
    h = a.h
    a.rect(5, 8, 54, h - 8, dk(SLATE, 0.15))
    a.rect(7, 10, 50, h - 12, dk(SLATE, 0.05))
    for x in range(10, 56, 7):
        a.vline(x, 11, h - 4, dk(SLATE, 0.28))
        a.vline(x + 1, 11, h - 4, li(SLATE, 0.10))
    a.rect(7, h - 22, 50, 9, mix(AMBER, SAND, 0.25))
    for x in range(7, 58, 9):
        a.poly([(x, h - 22), (x + 5, h - 22), (x + 11, h - 13), (x + 6, h - 13)],
               dk(COCOA, 0.30))
    a.hline(7, 56, h - 22, li(AMBER, 0.30))
    # lid
    a.rect(2, 0, 60, 9, mix(FOG, SILVER, 0.35))
    a.hline(2, 61, 0, WHITE)
    a.hline(2, 61, 1, li(SILVER, 0.40))
    a.hline(2, 61, 8, dk(FOG, 0.35))
    a.rect(26, 3, 12, 4, dk(STEEL, 0.30))
    a.hline(26, 37, 3, li(STEEL, 0.25))
    a.rect(29, 7, 9, 5, dk(PLUM, 0.45))          # bag peeking
    a.px(30, 8, mix(PLUM, WHITE, 0.35))
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