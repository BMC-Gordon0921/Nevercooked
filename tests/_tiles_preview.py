"""Quick look at walls/floors/decks: a 1x room mock and a 3x texture strip."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
from core import config

pygame.init()
A = config.ART_DIR
T = 64


def img(k):
    return pygame.image.load(os.path.join(A, k + ".png"))


def room_mock():
    W, H = 16 * T, 9 * T
    s = pygame.Surface((W, H))
    deck = [img("deck_a"), img("deck_b")]
    for ty in range(9):
        for tx in range(16):
            s.blit(deck[(tx + ty) % 2], (tx * T, ty * T))
    fl = [img("floor_a"), img("floor_b")]
    for ty in range(1, 8):
        for tx in range(1, 15):
            s.blit(fl[(tx + ty) % 2], (tx * T, ty * T))
    wb, ws, wf = img("wall_back"), img("wall_side"), img("wall_front")
    for tx in range(16):
        s.blit(wb, (tx * T, 2 * T - wb.get_height()))
    for ty in range(1, 8):
        s.blit(ws, (0, ty * T + T - ws.get_height()))
        s.blit(ws, (15 * T, ty * T + T - ws.get_height()))
    for tx in range(16):
        s.blit(wf, (tx * T, 9 * T - wf.get_height()))
    pygame.image.save(s, "tests/_room_mock.png")


def strip():
    names = ["floor_a", "floor_b", "deck_a", "deck_b"]
    Z = 4
    cell = T * Z
    s = pygame.Surface((cell * 2 + 24, cell * 2 + 24 + 0))
    s.fill((60, 60, 60))
    for i, n in enumerate(names):
        x = 8 + (i % 2) * (cell + 8)
        y = 8 + (i // 2) * (cell + 8)
        tile = pygame.transform.scale(img(n), (cell, cell))
        s.blit(tile, (x, y))
    pygame.image.save(s, "tests/_tile_strip.png")


room_mock()
strip()
print("ok")
