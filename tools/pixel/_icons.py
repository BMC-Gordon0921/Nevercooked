import os, sys
os.environ['SDL_VIDEODRIVER']='dummy'
sys.path.insert(0, os.getcwd())
import pygame; pygame.init()
from core import assets, config
names = [d["icon"] for d in config.ITEMS.values()]
uniq = []
for n in names:
    if n not in uniq:
        uniq.append(n)
S = 4
cell = 32 * S + 8
cols = 7
rows = (len(uniq) + cols - 1) // cols
out = pygame.Surface((cols * cell, rows * cell))
out.fill((236, 226, 206))
for i, key in enumerate(uniq):
    img = assets.image(key, (32, 32))
    big = pygame.transform.scale(img, (32*S, 32*S))
    x = (i % cols) * cell + 4
    y = (i // cols) * cell + 4
    out.blit(big, (x, y))
pygame.image.save(out, "tests/icons.png")
print(len(uniq), "icons", out.get_size())
