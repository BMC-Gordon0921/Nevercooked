import os, sys
os.environ['SDL_VIDEODRIVER'] = 'dummy'
sys.path.insert(0, os.getcwd())
import pygame; pygame.init()
from core import config
keys = ["station_crate","station_steamer","station_wok","station_oven","station_board","station_assemble","station_serve","station_trash"]
S = 3
sheet_w = 8 * (64*S + 10) + 10
sheet_h = 76*S + 70
sheet = pygame.Surface((sheet_w, sheet_h))
floor = pygame.image.load("assets/art/floor_a.png")
for x in range(0, sheet_w, 64):
    for y in range(0, sheet_h, 64):
        sheet.blit(floor, (x, y))
for i, k in enumerate(keys):
    img = pygame.image.load("assets/art/%s.png" % k)
    big = pygame.transform.scale(img, (img.get_width()*S, img.get_height()*S))
    x = 10 + i * (64*S + 10)
    y = sheet_h - 20 - big.get_height()
    sheet.blit(big, (x, y))
    label = pygame.font.SysFont("msyh", 16).render(k.replace("station_",""), True, (20,20,20))
    sheet.blit(label, (x + 10, sheet_h - 18))
pygame.image.save(sheet, "tests/stations_contact.png")
print(sheet.get_size())
