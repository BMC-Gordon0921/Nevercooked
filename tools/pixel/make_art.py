"""Draw the eight kitchen stations, at their real gameplay size.

The previous pass built 88-128px boxes and squeezed them onto 48-76px rows with a
nearest-neighbour row blit, so every feature collapsed into a horizontal stripe.
This generator draws each station *at its final size* instead:

    64 wide, exactly the height data/stations.json asks for, feet on the last
    row, one flat contact shadow on the floor.

One shared language, so the eight read as a single kitchen line:

    counter   the top band: fog slab inset 2px, 2px silver back edge, 2px steel
              front lip, slate seam under it
    front     steel face, 2px side walls (slate left, night right, lit from the
              upper left)
    plinth    6px night kick recessed 3px, so the floor shadow shows as wings
    outline   1px ink
    prop      one saturated thing on the counter that says what the machine is

Everything is drawn at final size with exact data/palette.json colours, so
px.finish only has to add the outline: no colour guessing, no rescaling.  The
game draws the world at 2x with a nearest-neighbour recenter, so every detail
here is at least 2px wide.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from core import config
from tools.pixel import pxlib as px
from tools.pixel.pxlib import Art, col

C = col
ART = config.ART_DIR

T = 64                  # canvas width: one tile
X0, X1 = 2, 61          # body columns; the ink outline lands on 1 and 62
WALL = 2                # side wall thickness
PLINTH = 6              # recessed kick height
PLINTH_IN = 3           # kick inset, each side

# --- shared metal ladder (every station is built from these six steps) --------
INK, VOID, NIGHT = C("ink"), C("void"), C("night")
SLATE, STEEL, FOG, SILVER = C("slate"), C("steel"), C("fog"), C("silver")

# --- warm metal, bamboo and produce ------------------------------------------
CREAM, SAND, CLAY = C("cream"), C("sand"), C("clay")
COCOA, WOOD = C("cocoa"), C("wood")
AMBER, YOLK = C("amber"), C("yolk")
FLAME, FLAME_D, FLAME_L = C("flame"), C("flame_deep"), C("flame_light")
TOMATO, LIME, LEAF = C("tomato"), C("lime"), C("leaf")
CYAN, GLOW = C("cyan"), C("glow")
MIST, STEAM = C("mist"), C("steam")

METAL = ["ink", "void", "night", "slate", "steel", "fog", "silver"]


# ------------------------------------------------------------------ the kit
def shadow(a):
    """Flat contact ellipse; the recessed plinth leaves its two wings visible."""
    a.ellipse(1, a.h - 6, 62, 6, VOID)


def body(a, y0, y1, front=STEEL, left=SLATE, right=NIGHT):
    """Front face with 2px side walls: the light comes from the upper left."""
    hh = y1 - y0 + 1
    a.rect(X0, y0, X1 - X0 + 1, hh, front)
    a.rect(X0, y0, WALL, hh, left)
    a.rect(X1 - WALL + 1, y0, WALL, hh, right)


def kick(a, y0):
    """Recessed plinth: darkest step, inset so the floor shadow reads."""
    x0, x1 = X0 + PLINTH_IN, X1 - PLINTH_IN
    a.rect(x0, y0, x1 - x0 + 1, PLINTH, NIGHT)
    a.rect(x0, y0, x1 - x0 + 1, 2, SLATE)


def counter(a, y0, band):
    """Top face: fog surface inset 2px, lit back edge, steel lip, slate seam."""
    a.rect(X0, y0, X1 - X0 + 1, band, SLATE)                  # wall tops at the sides
    a.rect(X0 + 2, y0, X1 - X0 - 3, band - 2, FOG)            # the surface itself
    a.rect(X0 + 2, y0, X1 - X0 - 3, 2, SILVER)                # specular back edge
    a.rect(X0, y0 + band - 3, X1 - X0 + 1, 2, STEEL)          # front lip
    a.hline(X0, X1, y0 + band - 1, SLATE)                     # seam under the lip


def lamp(a, x, y, c):
    """2x2 status LED in a 4x4 dark bezel: still a dot at 2x on screen."""
    a.rect(x, y, 4, 4, NIGHT)
    a.rect(x + 1, y + 1, 2, 2, c)


def knob(a, x, y, size=8, c=AMBER):
    """Chunky control knob with a dark bezel and a lit cap."""
    a.rect(x, y, size, size, SLATE)
    a.rect(x + 1, y + 1, size - 2, size - 2, c)
    a.rect(x + 2, y + 1, size - 4, 2, SILVER)


def grille(a, x, y, w, rows, step=4):
    """Air slots: dark gaps with a lit lip under each one."""
    a.rect(x, y, w, rows * step, NIGHT)
    for i in range(rows):
        a.rect(x, y + i * step, w, 2, VOID)
        a.rect(x, y + i * step + 2, w, 1, SLATE)


def panel(a, x, y, w, hh, face=SLATE, hi=FOG, lo=NIGHT):
    """Recessed panel: dark at the top, lit at the bottom (inverse bevel)."""
    a.rect(x, y, w, hh, face)
    a.rect(x, y, w, 2, lo)
    a.rect(x, y + hh - 2, w, 2, hi)


def handle(a, x, y, w, c=SILVER):
    """Drawer pull: 2px bar with dark ends."""
    a.rect(x - 2, y, w + 4, 2, NIGHT)
    a.rect(x, y, w, 2, c)


# ------------------------------------------------------------------ stations
def station_crate():
    """Ingredient hopper: open steel bin, sacks of produce, front chute."""
    a = Art(T, 54)
    h = a.h
    shadow(a)

    bt, band = 10, 11            # top band = the open hopper mouth
    bb = bt + band - 1           # 20
    fy = bb + 1                  # 21
    pt = h - PLINTH              # 48

    # the mouth (this station's top face), then the sacks sitting in it
    a.rect(X0, bt, X1 - X0 + 1, band, FOG)
    a.rect(X0, bt, X1 - X0 + 1, 2, SILVER)
    a.rect(X0 + 4, bt + 2, X1 - X0 - 7, band - 3, NIGHT)
    a.rect(X0 + 4, bt + 2, X1 - X0 - 7, 2, VOID)
    a.hline(X0, X1, bb, SLATE)

    for x, y, w, hh, lit, shade in ((10, bt - 7, 17, 15, CREAM, SAND),
                                    (28, bt - 4, 18, 12, SAND, CREAM),
                                    (46, bt - 1, 12, 9, CREAM, SAND)):
        a.ellipse(x, y, w, hh, shade)
        a.ellipse(x + 1, y, w - 2, hh - 2, lit)
        a.rect(x + 3, y + 2, 3, 3, NIGHT)                      # sack tie
    a.rect(14, bt - 3, 2, 2, LIME)
    a.rect(19, bt - 5, 2, 2, LIME)
    a.rect(33, bt, 2, 2, TOMATO)
    a.rect(37, bt + 2, 2, 2, TOMATO)
    a.rect(48, bt + 1, 2, 2, LIME)

    # --- front
    body(a, fy, pt - 1)
    a.rect(X0 + 2, fy, X1 - X0 - 3, 2, FOG)
    a.rect(X0 + 2, fy + 2, X1 - X0 - 3, 2, SLATE)
    for sx in (9, 50):
        a.rect(sx, fy + 4, 4, pt - fy - 6, SLATE)
        a.rect(sx, fy + 4, 2, pt - fy - 6, FOG)
        a.rect(sx + 1, fy + 6, 2, 2, SILVER)
        a.rect(sx + 1, pt - 8, 2, 2, SILVER)
    # produce label
    a.rect(21, 26, 22, 11, CREAM)
    a.rect(21, 26, 22, 2, SAND)
    a.rect(24, 28, 4, 4, TOMATO)
    a.rect(30, 29, 10, 2, LIME)
    a.rect(30, 33, 7, 2, LIME)
    # dispense chute
    a.rect(22, 40, 20, 4, NIGHT)
    a.rect(22, 40, 20, 2, VOID)
    a.rect(20, 44, 24, 2, SILVER)

    kick(a, pt)
    return px.finish(a, METAL + ["cream", "sand", "lime", "tomato"])


def basket(a, x0, x1, y0, y1):
    """One bamboo tier: cream slats, amber lit rim, clay foot, sand weave."""
    a.rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1, CREAM)
    a.rect(x0, y0, x1 - x0 + 1, 2, AMBER)
    a.rect(x0, y1 - 2, x1 - x0 + 1, 2, CLAY)
    for x in range(x0 + 4, x1 - 2, 8):
        a.rect(x, y0 + 2, 2, y1 - y0 - 4, SAND)


def station_steamer():
    """Bamboo steamer stack on a steel steaming cabinet."""
    a = Art(T, 72)
    h = a.h
    shadow(a)

    bt, band = 18, 12            # steel work top
    bb = bt + band - 1           # 29
    fy = bb + 1                  # 30
    pt = h - PLINTH              # 66

    # steam first: it rises behind and beside the baskets
    a.steam(11, 4, 15, MIST, MIST, seed=3, width=2)
    a.steam(53, 6, 13, MIST, MIST, seed=7, width=2)

    counter(a, bt, band)

    # --- the stack: lid, then two tiers, feet on the counter line
    a.rect(28, 2, 8, 3, CLAY)                                  # knob
    a.rect(28, 2, 8, 1, SAND)
    a.rrect(13, 5, 38, 7, CLAY, 3)                             # lid dome
    a.rect(15, 5, 34, 2, AMBER)
    a.rect(14, 9, 36, 2, SAND)
    basket(a, 11, 52, 11, 17)
    basket(a, 10, 53, 17, 23)
    a.rect(10, 24, 44, 2, SLATE)                               # contact shadow
    a.rect(12, 26, 40, 2, CLAY)                                # foot ring

    # --- front: steaming cabinet
    body(a, fy, pt - 1)
    a.rect(X0 + 2, fy, X1 - X0 - 3, 2, FOG)
    a.rect(X0 + 2, fy + 2, X1 - X0 - 3, 2, SLATE)
    # control row
    grille(a, 10, 36, 14, 3, step=4)
    knob(a, 30, 34, 8, AMBER)
    lamp(a, 47, 35, CYAN)
    a.rect(52, 34, 4, 8, NIGHT)
    a.rect(52, 34, 4, 2, SILVER)
    # big hob door with a lit seam
    panel(a, 8, 44, 48, 14, SLATE, FOG, NIGHT)
    a.rect(10, 47, 44, 2, STEEL)
    a.rect(10, 52, 44, 2, NIGHT)
    handle(a, 26, 57, 12)
    a.rect(9, 62, 46, 2, SLATE)

    kick(a, pt)
    return px.finish(a, METAL + ["cream", "sand", "clay", "amber", "mist"])


def station_wok():
    """Carbon-steel wok over a flame ring, on a steel range."""
    a = Art(T, 62)
    h = a.h
    shadow(a)

    bt, band = 15, 10
    bb = bt + band - 1           # 24
    fy = bb + 1                  # 25
    pt = h - PLINTH              # 56

    counter(a, bt, band)

    # burner ring and the flames that escape around the bowl
    a.ellipse(9, 18, 46, 9, NIGHT)
    for fx in (13, 21, 30, 39, 47):
        a.rect(fx, 20, 5, 4, FLAME_D)
        a.rect(fx + 1, 18, 3, 3, FLAME)
        a.rect(fx + 2, 17, 2, 2, FLAME_L)

    # the wok: dark bowl, 2px lit rim, fire and food inside
    a.ellipse(8, 6, 48, 18, SLATE)
    a.ring(8, 6, 48, 18, FOG, 2)
    a.ellipse(13, 8, 38, 9, NIGHT)
    a.ellipse(16, 9, 32, 7, FLAME_D)
    a.ellipse(20, 10, 24, 5, FLAME)
    a.ellipse(25, 11, 14, 3, FLAME_L)
    a.rect(24, 10, 2, 2, FLAME_L)
    a.rect(31, 12, 2, 2, TOMATO)
    a.rect(36, 10, 2, 2, LIME)
    for hx, tone in ((1, SLATE), (55, NIGHT)):
        a.rect(hx, 12, 8, 4, tone)
        a.rect(hx, 12, 8, 2, FOG)

    # --- front: the range
    body(a, fy, pt - 1)
    a.rect(X0 + 2, fy, X1 - X0 - 3, 2, FOG)
    a.rect(X0 + 2, fy + 2, X1 - X0 - 3, 2, SLATE)
    knob(a, 11, 33, 10, AMBER)
    a.rect(11, 31, 10, 2, FLAME_L)
    grille(a, 34, 32, 16, 3, step=5)
    lamp(a, 55, 30, AMBER)
    # grease tray
    a.rect(11, 45, 42, 5, NIGHT)
    a.rect(11, 45, 42, 2, VOID)
    a.rect(13, 50, 38, 2, SLATE)
    handle(a, 27, 53, 10)

    kick(a, pt)
    return px.finish(a, METAL + ["tomato", "flame_deep", "flame",
                                 "flame_light", "amber"])


def station_oven():
    """Tall oven: hot top, control row, glowing door, drawer under it."""
    a = Art(T, 76)
    h = a.h
    shadow(a)

    bt, band = 2, 15
    bb = bt + band - 1           # 16
    fy = bb + 1                  # 17
    pt = h - PLINTH              # 70

    # hot top: a slate plate set into the steel work top
    counter(a, bt, band)
    a.rect(6, 4, 52, 8, SLATE)
    a.rect(6, 4, 52, 2, NIGHT)
    a.rect(20, 6, 24, 4, NIGHT)
    for gx in (22, 30, 38):
        a.rect(gx, 7, 4, 2, FLAME_D)
    a.rect(56, 11, 2, 2, AMBER)

    # --- front
    body(a, fy, pt - 1)
    a.rect(X0 + 2, fy, X1 - X0 - 3, 2, FOG)
    # control row
    a.rect(X0 + 2, fy + 2, X1 - X0 - 3, 10, SLATE)
    knob(a, 8, 18, 6, AMBER)
    a.rect(20, 19, 16, 5, NIGHT)
    a.rect(21, 20, 6, 3, AMBER)
    a.rect(29, 20, 5, 3, FLAME)
    knob(a, 42, 18, 6, AMBER)
    lamp(a, 53, 19, CYAN)

    # door
    a.rect(6, 30, 52, 34, FOG)
    a.rect(9, 33, 46, 28, SLATE)
    a.rect(9, 33, 46, 2, NIGHT)
    a.rect(12, 36, 40, 22, NIGHT)                             # window cavity
    a.rect(12, 48, 40, 8, FLAME_D)
    a.rect(12, 52, 40, 6, FLAME)
    a.rect(12, 55, 40, 3, AMBER)
    a.rect(12, 36, 40, 3, VOID)
    for ry in (43, 49):
        a.rect(12, ry, 40, 2, SILVER)                         # racks
    a.rect(17, 39, 10, 5, NIGHT)                              # tray silhouette
    a.rect(18, 39, 8, 2, AMBER)
    a.rect(32, 45, 12, 4, NIGHT)
    a.rect(33, 45, 10, 2, AMBER)
    a.rect(12, 36, 2, 16, MIST)                               # glass reflection
    # handle + hinges
    a.rect(12, 64, 4, 4, NIGHT)
    a.rect(48, 64, 4, 4, NIGHT)
    handle(a, 10, 61, 44)
    a.rect(6, 66, 52, 2, SLATE)

    # drawer
    panel(a, 8, 69, 48, 2, SLATE, FOG, NIGHT)
    a.rect(6, 68, 52, 2, SLATE)
    a.rect(24, 68, 16, 2, SILVER)

    kick(a, pt)
    return px.finish(a, METAL + ["amber", "flame_deep", "flame", "mist", "cyan"])


def station_board():
    """Cutting counter: board and knife on top, two cupboard doors below."""
    a = Art(T, 50)
    h = a.h
    shadow(a)

    bt, band = 7, 10
    bb = bt + band - 1           # 16
    fy = bb + 1                  # 17
    pt = h - PLINTH              # 44

    counter(a, bt, band)

    # board, knife and trimmings resting on the counter
    a.rrect(9, 5, 32, 9, CREAM, 2)
    a.rect(11, 5, 28, 2, CLAY)
    a.rect(11, 12, 28, 2, CLAY)
    a.rect(20, 3, 16, 3, SILVER)                              # blade
    a.rect(20, 5, 12, 2, FOG)                                 # blade shadow
    a.poly([(36, 3), (41, 4), (36, 6)], SILVER)               # tip
    a.rect(43, 2, 7, 4, CLAY)                                 # handle
    a.rect(43, 2, 7, 2, CREAM)
    a.rect(13, 11, 2, 2, LIME)
    a.rect(27, 12, 2, 2, TOMATO)
    a.rect(31, 10, 2, 2, LIME)

    # --- front: two cupboard doors
    body(a, fy, pt - 1)
    a.rect(X0 + 2, fy, X1 - X0 - 3, 2, FOG)
    a.rect(X0 + 2, fy + 2, X1 - X0 - 3, 2, SLATE)
    panel(a, 7, 21, 22, 18, SLATE, FOG, NIGHT)
    panel(a, 33, 21, 22, 18, SLATE, FOG, NIGHT)
    a.rect(25, 26, 2, 8, SILVER)                              # pulls
    a.rect(35, 26, 2, 8, SILVER)
    a.rect(7, 39, 22, 2, NIGHT)
    a.rect(33, 39, 22, 2, NIGHT)
    lamp(a, 54, 18, CYAN)

    kick(a, pt)
    return px.finish(a, METAL + ["cream", "clay", "lime", "tomato", "cyan"])


def station_assemble():
    """Assembly counter: tray of filled bowls on top, two wide drawers."""
    a = Art(T, 54)
    h = a.h
    shadow(a)

    bt, band = 9, 11
    bb = bt + band - 1           # 19
    fy = bb + 1                  # 20
    pt = h - PLINTH              # 48

    counter(a, bt, band)

    # tray of bowls
    a.rect(9, 13, 46, 4, SILVER)
    a.rect(9, 13, 46, 2, FOG)
    a.rect(11, 16, 42, 2, NIGHT)
    for bx, by, bw, tone, dot in ((13, 7, 12, CREAM, TOMATO),
                                  (27, 6, 13, SILVER, LIME),
                                  (42, 8, 11, CREAM, AMBER)):
        a.rect(bx, by + 2, bw, 5, tone)
        a.rect(bx, by, bw, 2, SAND if tone is CREAM else FOG)
        a.rect(bx - 1, by - 2, bw + 2, 2, tone)
        a.rect(bx + 3, by - 1, 3, 2, dot)

    # --- front
    body(a, fy, pt - 1)
    a.rect(X0 + 2, fy, X1 - X0 - 3, 2, FOG)
    a.rect(X0 + 2, fy + 2, X1 - X0 - 3, 2, SLATE)
    for dy in (24, 35):
        panel(a, 7, dy, 50, 10, SLATE, FOG, NIGHT)
        a.rect(25, dy + 4, 14, 2, SILVER)
        a.rect(25, dy + 4, 14, 2, SILVER)
    a.rect(7, 46, 50, 2, SLATE)
    lamp(a, 54, 21, AMBER)

    kick(a, pt)
    return px.finish(a, METAL + ["cream", "sand", "amber", "tomato", "lime"])


def station_serve():
    """Pass-through hatch: lit opening, tray on the sill, tickets below."""
    a = Art(T, 56)
    h = a.h
    shadow(a)

    bt, band = 2, 11
    bb = bt + band - 1           # 12
    fy = bb + 1                  # 13
    pt = h - PLINTH              # 50

    counter(a, bt, band)

    # --- front
    body(a, fy, pt - 1)
    a.rect(X0 + 2, fy, X1 - X0 - 3, 2, FOG)
    a.rect(X0 + 2, fy + 2, X1 - X0 - 3, 2, SLATE)

    # the hatch: neon rim, warm cavity, tray on the sill
    a.rect(5, 18, 54, 20, CYAN)
    a.rect(7, 20, 50, 16, NIGHT)
    a.rect(9, 22, 46, 6, SLATE)
    a.rect(9, 30, 46, 4, FLAME)
    a.rect(9, 26, 46, 3, SLATE)
    a.rect(13, 26, 38, 8, NIGHT)                              # tray back
    a.rect(11, 30, 42, 4, SILVER)                             # tray
    a.rect(11, 30, 42, 2, FOG)
    a.rect(20, 27, 22, 5, CREAM)                              # plate
    a.rect(23, 27, 6, 2, AMBER)
    a.rect(31, 28, 4, 2, AMBER)
    a.rect(9, 34, 46, 2, AMBER)

    # sill
    a.rect(3, 38, 58, 3, FOG)
    a.rect(3, 38, 58, 2, SILVER)
    a.rect(3, 40, 58, 2, SLATE)

    # counter front with a ticket rail
    a.rect(X0, 42, X1 - X0 + 1, pt - 42, STEEL)
    a.rect(X0, 42, WALL, pt - 42, SLATE)
    a.rect(X1 - WALL + 1, 42, WALL, pt - 42, NIGHT)
    a.rect(X0 + 2, 42, X1 - X0 - 3, 2, CYAN)
    a.rect(X0 + 2, 44, X1 - X0 - 3, 2, SLATE)
    a.rect(8, 44, 52, 1, NIGHT)
    for tx in (12, 32):
        a.rect(tx, 44, 12, 6, CREAM)
        a.rect(tx + 2, 46, 8, 1, SLATE)
        a.rect(tx + 2, 48, 6, 1, SLATE)

    kick(a, pt)
    return px.finish(a, METAL + ["cream", "amber", "flame", "cyan"])


def station_trash():
    """Compactor bin: domed lid, hazard band, foot pedal."""
    a = Art(T, 48)
    h = a.h
    shadow(a)

    bt, band = 6, 10
    bb = bt + band - 1           # 15
    fy = bb + 1                  # 16
    pt = h - PLINTH              # 42

    # lid = this station's top face, with a grab handle above it
    a.rect(26, 2, 12, 4, SLATE)
    a.rect(26, 2, 12, 2, FOG)
    a.rrect(4, 6, 56, 10, FOG, 3)
    a.rect(7, 6, 50, 2, SILVER)
    a.rect(4, 13, 56, 2, STEEL)
    a.hline(4, 59, 15, SLATE)
    a.rect(9, 16, 46, 3, VOID)                                # mouth

    # --- body
    body(a, 19, pt - 1)
    for rx in (11, 50):
        a.rect(rx, 19, 2, 10, SLATE)
        a.rect(rx, 19, 2, 2, FOG)
    # hazard band
    a.rect(X0, 29, X1 - X0 + 1, 10, AMBER)
    for i in range(-10, 62, 12):
        a.poly([(X0 + i, 38), (X0 + i + 5, 38), (X0 + i + 10, 30), (X0 + i + 5, 30)], NIGHT)
    a.rect(X0, 29, X1 - X0 + 1, 2, YOLK)
    a.rect(X0, 38, X1 - X0 + 1, 2, FLAME_D)
    # pedal
    a.rect(14, 39, 24, 3, NIGHT)
    a.rect(14, 39, 24, 2, SILVER)
    a.rect(36, 41, 8, 2, SLATE)

    kick(a, pt)
    return px.finish(a, METAL + ["amber", "yolk", "flame_deep"])


STATIONS = {
    "station_crate": station_crate,
    "station_steamer": station_steamer,
    "station_wok": station_wok,
    "station_oven": station_oven,
    "station_board": station_board,
    "station_assemble": station_assemble,
    "station_serve": station_serve,
    "station_trash": station_trash,
}

# Height is owned by data/stations.json: the sprite must match it exactly, since
# the entity anchors the sprite's bottom-centre on the tile and uses the same
# number for occlusion and the progress bar above the machine.
TARGET = {key: config.STATION_DEFS[key[len("station_"):]]["height"] for key in STATIONS}


def main():
    pygame.init()
    os.makedirs(ART, exist_ok=True)
    for key, fn in STATIONS.items():
        art = fn()
        want = (T, TARGET[key])
        assert art.s.get_size() == want, (key, art.s.get_size(), want)
        px.save(art, os.path.join(ART, key + ".png"))
        s = px.stats(art)
        print("%-16s %2dx%-3d colours=%2d coverage=%.2f edge=%.1f lum=%.0f"
              % (key, s["size"][0], s["size"][1], s["colours"], s["coverage"],
                 s["edge"], s["lum"]))


if __name__ == "__main__":
    main()
