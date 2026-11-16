import sys, os
sys.path.insert(0, os.getcwd())
import pygame
pygame.init()
from tools.pixel import pxlib as px
from tools.pixel.make_tiles import deck_tile, floor_tile
from core import config
print("SAND", config.PALETTE.get("sand"), "STEEL", config.PALETTE.get("steel"))
for name, fn in (("deck", deck_tile), ("floor", floor_tile)):
    a = fn(True)
    from collections import Counter
    c = Counter()
    for y in range(a.h):
        for x in range(a.w):
            c[a.s.get_at((x, y))[:3]] += 1
    print(name, len(c), c.most_common(6))
