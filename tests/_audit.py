import json, os, sys
sys.path.insert(0, ".")
import pygame
pygame.init()
from core import config

def _rgb(v):
    if isinstance(v, str):
        v = v.lstrip("#")
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    return tuple(v)


pal = {_rgb(v) for v in json.load(open("data/palette.json", encoding="utf-8"))["names"].values()}
expect = {
    "wall_back": (64, 120), "wall_side": (64, 120), "wall_front": (64, 44),
    "floor_a": (64, 64), "floor_b": (64, 64), "deck_a": (64, 64), "deck_b": (64, 64),
    "chef": (528, 64), "_sheet": None,
}
for s in ["crate", "steamer", "wok", "oven", "board", "assemble", "serve", "trash"]:
    expect["station_" + s] = (64, None)
for i in ["rice", "rice_steamed", "egg", "stardust", "dough", "bun", "meat", "meat_cut",
          "veg", "veg_cut", "fried_rice", "roujiamo", "salad"]:
    expect["item_" + i] = (28, 28)

rows = []
bad = []
for key, exp in expect.items():
    exp = exp or (None, None)
    path = os.path.join(config.ART_DIR, key + ".png")
    if not os.path.exists(path):
        bad.append("MISSING " + key)
        continue
    surf = pygame.image.load(path)
    w, h = surf.get_size()
    cols = set()
    for y in range(h):
        for x in range(w):
            c = surf.get_at((x, y))
            if c.a > 0:
                cols.add((c.r, c.g, c.b))
    off = [c for c in cols if c not in pal]
    ok = (exp[0] is None or w == exp[0]) and (exp[1] is None or h == exp[1])
    if not ok:
        bad.append("%s size %dx%d != %s" % (key, w, h, exp))
    if len(cols) > 12:
        bad.append("%s colours %d>12" % (key, len(cols)))
    if off:
        bad.append("%s off-palette %s" % (key, off[:3]))
    rows.append("%-18s %3dx%-3d colours=%2d" % (key, w, h, len(cols)))
print("\n".join(rows))
print("BAD:", bad if bad else "none")
