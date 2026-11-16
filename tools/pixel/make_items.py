"""Generate the 13 item icons (28x28)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from core import config
from tools.pixel import pxlib as px
from tools.pixel.pxlib import Art, col, dk, li, mix
from tools.pixel._blocks import new_item_veg

C = col
ART = config.ART_DIR
IVORY, SAND, CREAM = C("ivory"), C("sand"), C("cream")
COCOA, LEATHER = C("cocoa"), C("leather")
MINT, TEAL, GLASS = C("mint"), C("teal"), C("glass")
STEEL_L, SILVER = C("steel_light"), C("silver")
AMBER, TOMATO, LEAF, LIME, YOLK = C("amber"), C("tomato"), C("leaf"), C("lime"), C("yolk")


def item_rice(a):
    a.ellipse(4, 12, 20, 15, SAND)
    a.rect(6, 12, 16, 12, SAND)
    a.ellipse(5, 13, 18, 13, mix(SAND, IVORY, 0.40))
    a.rect(7, 8, 14, 6, mix(SAND, COCOA, 0.30))
    a.ellipse(8, 7, 12, 6, mix(IVORY, SAND, 0.15))
    for x, y in ((10, 8), (13, 7), (16, 8), (12, 10), (15, 10), (9, 10)):
        a.px(x, y, IVORY)
        a.px(x, y + 1, mix(IVORY, SAND, 0.30))
    a.hline(7, 20, 13, dk(SAND, 0.25))
    a.hline(7, 20, 14, li(SAND, 0.30))
    a.rect(10, 17, 8, 5, TEAL)
    a.hline(11, 16, 19, MINT)
    a.vline(6, 15, 23, dk(SAND, 0.20))
    a.vline(21, 15, 23, dk(SAND, 0.35))
    a.hline(6, 21, 24, dk(SAND, 0.40))
    return px.finish(a, ["ink", "sand", "ivory", "cream", "cocoa", "teal", "mint", "wood", "fog"])


def item_rice_steamed(a):
    a.steam(14, 1, 6, C("white"), C("steam"), seed=2, width=2)
    a.ellipse(3, 12, 22, 13, STEEL_L)
    a.ellipse(4, 13, 20, 11, mix(STEEL_L, SILVER, 0.5))
    a.ellipse(4, 13, 20, 4, mix(STEEL_L, SILVER, 0.25))
    a.ellipse(6, 9, 16, 10, IVORY)
    a.ellipse(7, 10, 14, 8, C("white"))
    a.ellipse(8, 11, 12, 6, IVORY)
    for x, y in ((9, 12), (12, 11), (15, 12), (18, 13), (11, 14), (16, 15)):
        a.px(x, y, mix(IVORY, SAND, 0.35))
    a.hline(9, 18, 9, C("white"))
    a.hline(4, 23, 21, dk(STEEL_L, 0.30))
    a.hline(6, 21, 23, dk(STEEL_L, 0.45))
    return px.finish(a, ["ink", "steel_light", "silver", "steel", "ivory", "white", "sand", "cream", "steam", "mint"])


def item_egg(a):
    a.ellipse(6, 5, 16, 20, CREAM)
    a.ellipse(7, 6, 14, 18, IVORY)
    a.ellipse(8, 7, 10, 11, C("white"))
    a.ellipse(15, 14, 6, 8, mix(CREAM, SAND, 0.40))
    a.ellipse(9, 8, 5, 6, C("white"))
    a.px(11, 10, C("white"))
    for x, y in ((12, 20), (13, 19), (17, 21)):
        a.px(x, y, mix(CREAM, SAND, 0.55))
    a.hline(9, 19, 23, mix(CREAM, SAND, 0.50))
    return px.finish(a, ["ink", "cream", "ivory", "white", "sand", "fog"])


def item_dough(a):
    a.ellipse(2, 12, 24, 13, mix(CREAM, SAND, 0.65))
    a.ellipse(3, 12, 22, 11, mix(CREAM, SAND, 0.35))
    a.ellipse(5, 12, 18, 8, CREAM)
    a.ellipse(7, 13, 13, 5, IVORY)
    a.hline(9, 15, 16, mix(CREAM, SAND, 0.55))
    a.hline(7, 20, 18, mix(CREAM, SAND, 0.75))
    a.hline(4, 23, 22, mix(CREAM, SAND, 0.55))
    for x, y in ((10, 10), (16, 11), (19, 14), (6, 15), (21, 17), (12, 19)):
        a.px(x, y, C("white"))
    return px.finish(a, ["ink", "cream", "ivory", "white", "sand", "fog"])


def item_bun(a):
    a.ellipse(3, 6, 22, 18, CREAM)
    a.ellipse(4, 7, 20, 16, IVORY)
    a.ellipse(6, 7, 14, 10, C("white"))
    for sx, sy in ((9, 13), (13, 11), (17, 13)):
        a.line((sx, sy), (sx + 1, sy + 7), mix(CREAM, SAND, 0.55))
    a.line((14, 9), (14, 19), mix(CREAM, SAND, 0.65))
    a.hline(9, 18, 20, mix(CREAM, SAND, 0.60))
    a.hline(5, 22, 23, mix(CREAM, SAND, 0.55))
    a.px(14, 5, AMBER)
    a.px(15, 5, mix(AMBER, C("white"), 0.4))
    return px.finish(a, ["ink", "cream", "ivory", "white", "sand", "fog", "amber"])


def item_meat(a):
    a.poly([(3, 12), (7, 6), (17, 5), (23, 10), (22, 18), (16, 23), (7, 21), (4, 17)], TOMATO)
    a.poly([(5, 13), (8, 8), (16, 7), (21, 11), (20, 17), (15, 21), (8, 19)], mix(TOMATO, C("blush"), 0.28))
    a.poly([(7, 12), (11, 9), (16, 9), (14, 13), (9, 15)], mix(TOMATO, C("blush"), 0.50))
    a.line((9, 17), (14, 15), CREAM)
    a.line((13, 18), (17, 16), CREAM)
    a.line((11, 12), (16, 11), mix(CREAM, TOMATO, 0.35))
    a.hline(6, 20, 22, dk(TOMATO, 0.35))
    return px.finish(a, ["ink", "tomato", "blush", "cream", "leather", "cocoa", "wine", "fog", "sand"])


def item_veg_cut(a):
    for x, y, w, h in ((4, 12, 9, 9), (14, 14, 9, 8), (9, 5, 10, 8)):
        a.rect(x, y, w, h, LEAF if x != 14 else mix(LEAF, LIME, 0.30))
        a.rect(x, y, w, 3, LIME)
        a.rect(x, y, 3, h, mix(LEAF, LIME, 0.45))
        a.hline(x, x + w - 1, y + h - 1, C("ink"))
    for x, y in ((6, 15), (16, 17), (11, 8), (20, 16), (12, 15)):
        a.px(x, y, CREAM)
    a.hline(4, 22, 23, dk(LEAF, 0.35))
    return px.finish(a, ["ink", "leaf", "lime", "cream", "mint", "sand", "fog"])


def item_fried_rice(a):
    a.steam(14, 1, 6, C("white"), C("steam"), seed=4, width=2)
    a.ellipse(2, 15, 24, 11, SILVER)
    a.ellipse(3, 16, 22, 9, mix(SILVER, STEEL_L, 0.45))
    a.rect(12, 22, 4, 3, mix(SILVER, STEEL_L, 0.60))
    a.ellipse(5, 8, 18, 12, IVORY)
    a.ellipse(6, 9, 16, 10, mix(IVORY, SAND, 0.20))
    for x, y in ((9, 11), (13, 10), (17, 12), (11, 14), (15, 15), (19, 14)):
        a.px(x, y, AMBER)
    for x, y in ((12, 13), (16, 11), (10, 16)):
        a.px(x, y, LEAF)
    a.px(14, 12, YOLK)
    a.hline(3, 22, 24, dk(SILVER, 0.35))
    return px.finish(a, ["ink", "silver", "steel_light", "steel", "ivory", "sand", "amber", "yolk", "leaf", "steam", "white", "cream"])


def item_roujiamo(a):
    a.ellipse(2, 9, 24, 16, CREAM)
    a.ellipse(3, 10, 22, 14, mix(CREAM, SAND, 0.30))
    a.ellipse(4, 9, 20, 9, mix(CREAM, IVORY, 0.50))
    a.rect(4, 14, 20, 5, mix(COCOA, C("ink"), 0.30))
    for x in range(5, 23, 2):
        a.px(x, 15, mix(TOMATO, LEATHER, 0.50))
        a.px(x, 16, mix(LEATHER, COCOA, 0.40))
    a.px(8, 15, LEAF)
    a.px(16, 16, LEAF)
    a.hline(6, 20, 10, li(CREAM, 0.45))
    a.hline(4, 22, 12, mix(CREAM, SAND, 0.45))
    a.hline(4, 22, 21, mix(CREAM, SAND, 0.55))
    a.hline(5, 21, 23, dk(CREAM, 0.30))
    return px.finish(a, ["ink", "cream", "sand", "ivory", "white", "cocoa", "leather", "tomato", "leaf", "lime", "wood", "fog"])


def item_salad(a):
    a.ellipse(2, 12, 24, 13, MINT)
    a.ellipse(3, 13, 22, 11, mix(MINT, TEAL, 0.35))
    a.ellipse(4, 12, 20, 5, mix(MINT, IVORY, 0.50))
    a.ellipse(6, 7, 9, 8, LEAF)
    a.ellipse(12, 6, 10, 8, mix(LEAF, LIME, 0.50))
    a.ellipse(15, 9, 8, 6, LEAF)
    a.ellipse(7, 9, 6, 5, LIME)
    a.ellipse(9, 11, 5, 4, TOMATO)
    a.ellipse(17, 12, 4, 4, TOMATO)
    a.px(13, 12, YOLK)
    a.px(14, 13, YOLK)
    a.hline(4, 23, 20, li(MINT, 0.25))
    a.hline(5, 22, 22, dk(MINT, 0.30))
    a.hline(7, 20, 24, dk(MINT, 0.45))
    return px.finish(a, ["ink", "mint", "teal", "ivory", "leaf", "lime", "tomato", "yolk", "cream", "fog", "steel_light"])


def item_stardust(a):
    a.ellipse(4, 20, 20, 6, mix(TEAL, C("ink"), 0.55))
    a.poly([(14, 3), (21, 13), (18, 24), (10, 24), (8, 14)], TEAL)
    a.poly([(13, 6), (17, 12), (15, 21), (11, 19), (11, 12)], GLASS)
    a.poly([(17, 13), (19, 21), (16, 23)], mix(TEAL, C("mint"), 0.35))
    a.poly([(7, 13), (11, 17), (10, 24), (5, 22)], mix(TEAL, STEEL_L, 0.25))
    a.poly([(21, 15), (25, 19), (22, 24), (19, 22)], mix(TEAL, MINT, 0.30))
    a.px(12, 9, C("white"))
    a.px(13, 8, C("white"))
    a.px(15, 14, C("white"))
    for x, y in ((6, 8), (22, 7), (19, 3)):
        a.px(x, y, AMBER)
        a.px(x - 1, y, mix(AMBER, C("white"), 0.5))
        a.px(x + 1, y, mix(AMBER, C("white"), 0.5))
        a.px(x, y - 1, mix(AMBER, C("white"), 0.5))
        a.px(x, y + 1, mix(AMBER, C("white"), 0.5))
    a.hline(5, 22, 24, mix(TEAL, C("ink"), 0.45))
    return px.finish(a, ["ink", "teal", "mint", "glass", "white", "amber", "steel_light", "steel", "sand", "fog"])



def item_meat_cut(a):
    a.ellipse(3, 19, 22, 7, mix(TOMATO, C("ink"), 0.45))
    for x0, y0, w, h, tone in ((5, 12, 13, 8, mix(TOMATO, C("blush"), 0.30)),
                               (10, 7, 13, 8, mix(TOMATO, C("blush"), 0.50)),
                               (13, 15, 11, 7, mix(TOMATO, C("blush"), 0.15))):
        a.rrect(x0, y0, w, h, tone, 3)
        a.hline(x0 + 1, x0 + w - 2, y0, mix(tone, C("white"), 0.35))
        a.hline(x0 + 1, x0 + w - 2, y0 + h - 1, mix(tone, C("ink"), 0.30))
    a.line((7, 15), (15, 14), CREAM)
    a.line((12, 10), (20, 9), CREAM)
    a.line((15, 18), (22, 17), CREAM)
    a.px(9, 13, mix(TOMATO, C("blush"), 0.65))
    a.px(18, 11, mix(TOMATO, C("blush"), 0.65))
    return px.finish(a, ["ink", "tomato", "blush", "cream", "sand", "leather", "wood", "fog", "ivory"])



ITEMS = {
    "rice": item_rice, "rice_steamed": item_rice_steamed, "egg": item_egg,
    "stardust": item_stardust, "dough": item_dough, "bun": item_bun,
    "meat": item_meat, "meat_cut": item_meat_cut, "veg": lambda a: new_item_veg(),
    "veg_cut": item_veg_cut, "fried_rice": item_fried_rice,
    "roujiamo": item_roujiamo, "salad": item_salad,
}


def main():
    pygame.init()
    for name, fn in ITEMS.items():
        art = fn(Art(28, 28))
        assert art.s.get_size() == (28, 28), name
        px.save(art, os.path.join(ART, "item_" + name + ".png"))
        print("item_" + name, px.stats(art))
    strip = pygame.Surface((13 * 40, 40), pygame.SRCALPHA)
    for i, name in enumerate(ITEMS):
        surf = pygame.image.load(os.path.join(ART, "item_" + name + ".png"))
        strip.blit(pygame.transform.scale(surf, (36, 36)), (i * 40 + 2, 2))
    pygame.image.save(pygame.transform.scale(strip, (13 * 40 * 3, 120)), "tests/_item_strip.png")


if __name__ == "__main__":
    main()
