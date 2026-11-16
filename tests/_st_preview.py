import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
from core import config
pygame.init()
A = config.ART_DIR
T = 64
names = ["crate", "steamer", "wok", "oven", "board", "assemble", "serve", "trash"]
fa = pygame.image.load(os.path.join(A, "floor_a.png"))
fb = pygame.image.load(os.path.join(A, "floor_b.png"))
gap = 10
W = len(names) * (T + gap) + gap
H = 128 + 40
s = pygame.Surface((W, H))
for ty in range(H // T + 1):
    for tx in range(W // T + 1):
        s.blit(fa if (tx + ty) % 2 == 0 else fb, (tx * T, ty * T))
for i, n in enumerate(names):
    img = pygame.image.load(os.path.join(A, "station_" + n + ".png"))
    x = gap + i * (T + gap) + (T - img.get_width()) // 2
    y = H - 12 - img.get_height()
    s.blit(img, (x, y))
big = pygame.transform.scale(s, (W * 2, H * 2))
pygame.image.save(big, "tests/_st_preview.png")
print("ok", big.get_size())
