"""Build tests/_art_sheet.png (2x contact sheet) and assets/art/_sheet.png (1x)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from core import config
from core.text import render

pygame.init()
A = config.ART_DIR
Z = 2

TILES = ["wall_back", "wall_side", "wall_front", "floor_a", "floor_b", "deck_a", "deck_b"]
STATIONS = ["crate", "steamer", "wok", "oven", "board", "assemble", "serve", "trash"]
ITEMS = ["rice", "rice_steamed", "egg", "stardust", "dough", "bun", "meat", "meat_cut",
         "veg", "veg_cut", "fried_rice", "roujiamo", "salad"]

BG = (236, 231, 219)
INK = (46, 52, 64)


def load(name):
    return pygame.image.load(os.path.join(A, name + ".png"))


def build(scale):
    pad = 12 * scale
    lab = 14 * scale
    tw = 64 * scale
    rows = [172 * scale + lab, 132 * scale + lab, 64 * scale + lab, 70 * scale + lab]
    W = max(pad + 8 * (tw + pad), pad + len(TILES) * (tw + pad), pad + 13 * (28 * scale + pad))
    W = max(W, pad + 12 * (44 * scale + 6 * scale) + pad)
    H = sum(rows) + pad * 4
    s = pygame.Surface((W, H))
    s.fill(BG)
    fsz = max(9, 12 * scale // 2)

    def label(txt, x, y):
        s.blit(render(txt, fsz, INK), (x, y))

    def blit(name, x, y, w=None):
        img = load(name)
        if w:
            img = pygame.transform.scale(img, (w, int(img.get_height() * w / img.get_width())))
        else:
            img = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
        s.blit(img, (x, y))
        return img.get_size()

    # row 1: tiles
    x, y = pad, pad
    for n in TILES:
        if n == "wall_front":
            continue
        w, h = blit(n, x, y)
        label("%s %dx%d" % (n, w // scale, h // scale), x, y + h + 2)
        x += w + pad
    wf = load("wall_front")
    s.blit(pygame.transform.scale(wf, (64 * scale, 44 * scale)), (pad, y + 120 * scale + 18 * scale))
    label("wall_front 64x44", pad, y + (120 + 44) * scale + 20 * scale)

    # row 2: stations on floor
    y += rows[0]
    x = pad
    fa, fb = load("floor_a"), load("floor_b")
    for i, n in enumerate(STATIONS):
        img = load("station_" + n)
        w, h = img.get_size()
        patch = pygame.Surface((64, 64))
        patch.blit(fa if i % 2 == 0 else fb, (0, 0))
        s.blit(pygame.transform.scale(patch, (64 * scale, 64 * scale)), (x, y + (128 - 64) * scale))
        s.blit(pygame.transform.scale(img, (w * scale, h * scale)), (x + (64 - w) // 2 * scale, y + (128 - h) * scale))
        label("%s %dx%d" % (n, w, h), x, y + 128 * scale + 2)
        x += 64 * scale + pad

    # row 3: items
    y += rows[1]
    x = pad
    for n in ITEMS:
        blit("item_" + n, x, y, 28 * scale * 2)
        label(n, x, y + 56 * scale + 2)
        x += 58 * scale + pad

    # row 4: chef
    y += rows[2]
    cs = load("chef")
    for f in range(12):
        sub = cs.subsurface(pygame.Rect(f * 44, 0, 44, 64)).copy()
        s.blit(pygame.transform.scale(sub, (44 * scale, 64 * scale)), (pad + f * (44 * scale + 4 * scale), y))
    label("chef 528x64 = 12 frames of 44x64 (down x4, up x4, side x4)", pad, y + 64 * scale + 4)
    return s


sheet = build(2)
pygame.image.save(sheet, "tests/_art_sheet.png")
pygame.image.save(build(1), os.path.join(A, "_sheet.png"))

# scene mock: 5x4 room slice, wall on top, chef in front of a station
T = 64
mock = pygame.Surface((5 * T, 4 * T + 120))
mock.fill((11, 14, 20))
for tx in range(5):
    mock.blit(load("wall_back"), (tx * T, 0))
wall = load("wall_side")
for ty in range(6):
    mock.blit(wall, (0, 120 + ty * T - 56))
    mock.blit(wall, (4 * T, 120 + ty * T - 56))
for ty in range(4):
    for tx in range(5):
        mock.blit(load("floor_a") if (tx + ty) % 2 == 0 else load("floor_b"), (tx * T, 120 + ty * T))
st = load("station_wok")
mock.blit(st, (2 * T + (64 - st.get_width()) // 2, 120 + 1 * T + 64 - st.get_height()))
chef = load("chef").subsurface(pygame.Rect(0, 0, 44, 64)).copy()
mock.blit(chef, (2 * T + 10, 120 + 2 * T + 64 - 64))
pygame.image.save(pygame.transform.scale(mock, (mock.get_width() * 2, mock.get_height() * 2)), "tests/_scene_mock.png")
print("sheet", sheet.get_size(), "mock", mock.get_size())
