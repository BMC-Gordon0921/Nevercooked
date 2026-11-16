"""Bright space-canteen walls, floors and deck plates -> assets/art/.

Sizes are the contract the game loads by:  wall_back / wall_side 64x120,
wall_front 64x44, floor_* and deck_* 64x64.

Tiling contract (learned from game/world.py + render.py):
  * wall_back repeats HORIZONTALLY, so every vertical feature must sit on a
    32px rhythm and horizontal bands are safe.
  * wall_side repeats VERTICALLY once per 64px row, and a 120px sprite is
    anchored at its tile bottom, so only its top 64px survives (the next row
    covers the rest).  It therefore gets NO horizontal band above y=93 --
    otherwise the column turns into stripes.  Cap/skirting live at its foot.
  * floor_* / deck_* repeat in both directions: only 1px joins at the
    right/bottom edge, no gradients that reveal the grid.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from core import config
from tools.pixel import pxlib as px
from tools.pixel.pxlib import Art, col, dk, li, mix

C = col
ART = config.ART_DIR

WALL_W, WALL_H = 64, 120
FRONT_H = 44

IVORY, SAND, CREAM = C("ivory"), C("sand"), C("cream")
CLAY, WOOD, COCOA = C("clay"), C("wood"), C("cocoa")
MINT, TEAL, GLASS = C("mint"), C("teal"), C("glass")
GLOW, CYAN = C("glow"), C("cyan")
STEEL_L, SILVER, FOG, STEEL = C("steel_light"), C("silver"), C("fog"), C("steel")
INK = C("ink")


# --------------------------------------------------------------------- walls
def wall_back():
    """Cool metal bulkhead.  The floor is warm cream, so the wall must be cold:
    a cream wall over a cream floor reads as one endless plane."""
    a = Art(WALL_W, WALL_H)
    body = mix(SILVER, FOG, 0.45)
    a.fill(body)
    a.rect(0, 10, WALL_W, 96, body)

    # -- stiffener cap + neon eave --------------------------------------
    a.rect(0, 0, WALL_W, 1, INK)
    a.rect(0, 1, WALL_W, 4, STEEL)
    a.hline(0, WALL_W - 1, 1, li(STEEL, 0.35))
    a.hline(0, WALL_W - 1, 5, dk(STEEL, 0.35))
    a.rect(0, 6, WALL_W, 4, dk(mix(STEEL, FOG, 0.4), 0.10))
    a.hline(0, WALL_W - 1, 10, GLOW)
    a.hline(0, WALL_W - 1, 11, mix(GLOW, TEAL, 0.45))
    a.hline(0, WALL_W - 1, 12, INK)
    a.hline(0, WALL_W - 1, 13, mix(body, INK, 0.18))
    a.hline(0, WALL_W - 1, 14, li(body, 0.16))

    # -- panelled field: one joint per 32px, a horizontal rail at 58 ---
    for x0 in (0, 32):
        a.vline(x0, 14, 105, dk(body, 0.30))
        a.vline(x0 + 1, 14, 105, li(body, 0.40))
    a.rect(0, 56, WALL_W, 4, mix(body, STEEL, 0.35))
    a.hline(0, WALL_W - 1, 56, li(body, 0.25))
    a.hline(0, WALL_W - 1, 59, dk(body, 0.30))
    for x in (6, 38, 22, 54):
        a.rivet(x, 62)
    a.grime(0, 15, WALL_W, 88, body, FOG, density=0.010, seed=11)
    a.grime(0, 15, WALL_W, 88, body, C("white"), density=0.006, seed=12)
    a.grime(0, 96, WALL_W, 9, body, FOG, density=0.05, seed=19)

    # -- mint accent + dark skirting (6px) ------------------------------
    a.rect(0, 106, WALL_W, 5, MINT)
    a.hline(0, WALL_W - 1, 106, li(MINT, 0.35))
    a.hline(0, WALL_W - 1, 110, mix(TEAL, MINT, 0.35))
    a.rect(0, 111, WALL_W, 6, STEEL)
    a.hline(0, WALL_W - 1, 111, li(STEEL, 0.30))
    a.hline(0, WALL_W - 1, 112, mix(STEEL, SAND, 0.25))
    a.rect(0, 115, WALL_W, 3, dk(STEEL, 0.35))
    a.hline(0, WALL_W - 1, 118, dk(STEEL, 0.55))
    a.hline(0, WALL_W - 1, 119, INK)
    for x in (15, 47):
        a.px(x, 113, li(STEEL, 0.20))
    return px.finish(a, ["ink", "silver", "fog", "steel", "steel_light", "glow", "teal",
                         "mint", "white", "slate", "sand", "cream"])


def wall_side():
    """Continuous side wall.  Only the top 64px of this sprite is ever seen,
    so everything above the wainscot must be uniform along y."""
    a = Art(WALL_W, WALL_H)
    base = mix(SILVER, FOG, 0.55)
    a.fill(base)
    # light falls from the open side: brighten toward the room, shade the outer lip
    for x in range(WALL_W):
        t = abs(x - 44) / 44.0
        a.vline(x, 0, 105, mix(base, li(base, 0.22), max(0.0, 1.0 - t * 1.6)))
    # vertical features only: two panel joints and the shadowed outer lip
    for x0 in (9, 47):
        a.vline(x0, 0, 105, mix(base, dk(base, 0.18), 0.8))
        a.vline(x0 + 1, 0, 105, li(base, 0.30))
    a.vline(0, 0, 105, dk(base, 0.26))
    a.vline(1, 0, 105, dk(base, 0.12))
    a.vline(WALL_W - 1, 0, 105, dk(base, 0.18))
    a.grime(1, 0, WALL_W - 2, 105, base, FOG, density=0.025, seed=23)
    a.hline(0, WALL_W - 1, 104, dk(base, 0.10))
    # foot: wainscot + skirting, only the bottom-most side tile shows these
    a.rect(0, 106, WALL_W, 5, MINT)
    a.hline(0, WALL_W - 1, 106, li(MINT, 0.35))
    a.hline(0, WALL_W - 1, 110, mix(TEAL, MINT, 0.35))
    a.rect(0, 111, WALL_W, 6, STEEL)
    a.hline(0, WALL_W - 1, 111, li(STEEL, 0.30))
    a.hline(0, WALL_W - 1, 112, mix(STEEL, SAND, 0.25))
    a.rect(0, 115, WALL_W, 3, dk(STEEL, 0.35))
    a.hline(0, WALL_W - 1, 118, dk(STEEL, 0.55))
    a.hline(0, WALL_W - 1, 119, INK)
    return px.finish(a, ["ink", "steel_light", "ivory", "sand", "cream", "mint", "teal",
                         "steel", "fog", "silver", "glow", "clay"])


def wall_front():
    """Counter-height bar front with a neon lip."""
    a = Art(WALL_W, FRONT_H)
    a.rect(0, 0, WALL_W, 1, INK)
    a.rect(0, 1, WALL_W, 10, SAND)
    a.hline(0, WALL_W - 1, 1, li(SAND, 0.60))
    a.hline(0, WALL_W - 1, 2, li(SAND, 0.30))
    a.grime(2, 3, WALL_W - 4, 6, SAND, CREAM, density=0.07, seed=31)
    a.hline(0, WALL_W - 1, 11, GLOW)
    a.hline(0, WALL_W - 1, 12, mix(GLOW, TEAL, 0.5))
    a.hline(0, WALL_W - 1, 13, INK)
    # wood front, two planks
    a.rect(0, 14, WALL_W, 22, CLAY)
    for y0 in (14, 25):
        a.rect(0, y0, WALL_W, 10, CLAY if y0 == 14 else mix(CLAY, WOOD, 0.22))
        a.hline(0, WALL_W - 1, y0, li(CLAY, 0.40))
        a.hline(0, WALL_W - 1, y0 + 9, dk(CLAY, 0.28))
    for x in range(3, WALL_W, 7):
        for yy in range(16, 34, 3):
            if px.h2(x, yy, 41) > 0.5:
                a.px(x, yy, mix(CLAY, WOOD, 0.6))
    # dark plinth
    a.rect(0, 36, WALL_W, 7, STEEL)
    a.hline(0, WALL_W - 1, 36, li(STEEL, 0.32))
    a.rivet(6, 38)
    a.rivet(54, 38)
    a.rect(0, 40, WALL_W, 3, dk(STEEL, 0.40))
    a.hline(0, WALL_W - 1, 43, INK)
    return px.finish(a, ["ink", "sand", "cream", "ivory", "clay", "wood", "silver", "steel",
                         "glow", "teal", "mint", "steel_light"])


# --------------------------------------------------------------------- floors
def floor_tile(bright):
    """Quiet polished tile.  a/b differ by ~2% luminance: only the grain and
    the 1px cool join reveal the grid."""
    a = Art(px.TILE, px.TILE)
    base = mix(SAND, CREAM, 0.45) if bright else mix(SAND, CREAM, 0.30)
    a.fill(base)
    # fine terrazzo grain
    for y in range(px.TILE):
        for x in range(px.TILE):
            n = px.h2(x, y, 101 if bright else 202)
            if n < 0.020:
                a.px(x, y, mix(base, SAND, 0.45))
            elif n < 0.028:
                a.px(x, y, mix(base, STEEL_L, 0.55))
            elif n < 0.032:
                a.px(x, y, mix(base, CLAY, 0.25))
    # a few chips, barely there
    for x, y, w, h in ((9, 17, 2, 1), (33, 40, 2, 1), (44, 22, 1, 2),
                       (20, 49, 2, 1), (52, 30, 1, 1), (14, 33, 1, 1)):
        a.rect(x, y, w, h, mix(base, STEEL_L, 0.85))
    # thin scratches
    for i in range(4):
        x = 6 + int(px.h2(i, 3, 77) * 44)
        y = 8 + int(px.h2(i, 4, 77) * 44)
        ln = 3 + int(px.h2(i, 5, 77) * 3)
        a.hline(x, x + ln, y, mix(base, FOG, 0.30))
    # grout: two 32px cells per tile.  Without joints the floor reads as paper,
    # and the eye loses all sense of speed -- 2px of grout buys the whole floor.
    joint = mix(base, COCOA, 0.20)
    for x0 in (31, 63):
        a.vline(x0, 0, px.TILE - 1, joint)
    for y0 in (31, 63):
        a.hline(0, px.TILE - 1, y0, joint)
    # a touch of dirt where the grout meets the tiles
    a.grime(0, 0, px.TILE, px.TILE, base, SAND, density=0.012, seed=131 if bright else 232)
    return px.finish(a, ["ivory", "sand", "cream", "steel_light", "clay", "steel", "fog", "silver"])


def deck_tile(bright):
    """Dark warm concrete outside the kitchen: a recessed plate, not the floor."""
    a = Art(px.TILE, px.TILE)
    base = mix(STEEL, SAND, 0.22) if bright else mix(STEEL, SAND, 0.20)
    a.fill(base)
    light = mix(base, SILVER, 0.55)
    # broad concrete grain, no regular ribs (ribs read as blueprint paper)
    for y in range(px.TILE):
        for x in range(px.TILE):
            n = px.h2(x, y, 707 if bright else 808)
            if n < 0.045:
                a.px(x, y, mix(base, FOG, 0.35))
            elif n < 0.060:
                a.px(x, y, mix(base, SILVER, 0.22))
    # one recessed plate seam along the tile edge: two pixels, lip + shadow
    a.hline(0, px.TILE - 1, px.TILE - 2, light)
    a.hline(0, px.TILE - 1, px.TILE - 1, mix(base, INK, 0.45))
    a.vline(px.TILE - 1, 0, px.TILE - 1, mix(base, INK, 0.35))
    a.hline(0, px.TILE - 1, 0, mix(base, SILVER, 0.18))
    # wear
    for i in range(8):
        x = int(px.h2(i, 1, 303 if bright else 404) * 58) + 3
        y = int(px.h2(i, 2, 303 if bright else 404) * 58) + 3
        a.px(x, y, mix(base, FOG, 0.55))
        a.px(x + 1, y, mix(base, SILVER, 0.30))
    return px.finish(a, ["fog", "steel", "slate", "silver", "steel_light", "ink", "glass",
                         "mint", "sand", "cream", "ivory", "cocoa"])


def main():
    pygame.init()
    os.makedirs(ART, exist_ok=True)
    out = {
        "wall_back": (wall_back(), (64, 120)),
        "wall_side": (wall_side(), (64, 120)),
        "wall_front": (wall_front(), (64, 44)),
        "floor_a": (floor_tile(True), (64, 64)),
        "floor_b": (floor_tile(False), (64, 64)),
        "deck_a": (deck_tile(True), (64, 64)),
        "deck_b": (deck_tile(False), (64, 64)),
    }
    for key, (art, want) in out.items():
        assert art.s.get_size() == want, (key, art.s.get_size(), want)
        px.save(art, os.path.join(ART, key + ".png"))
        print("%-11s %s  %s" % (key, art.s.get_size(), px.stats(art)))


if __name__ == "__main__":
    main()
