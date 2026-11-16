import os, sys
os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0, os.getcwd())
import pygame; pygame.init(); pygame.display.set_mode((1280,720))
from scenes.game import GameScene
from game.systems import render
from core import config
class App:
    def switch(self,s): pass
g = GameScene(App()); w = g.world
for _ in range(5):
    g.update(1/60.0, __import__('core.input', fromlist=['Intent']).Intent())
surf = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
surf.fill((255,0,255))
render.draw_floor(surf, w, g.camera)
pygame.image.save(surf, "tests/dbg_floor.png")
render.draw_sorted(surf, w, g.camera)
pygame.image.save(surf, "tests/dbg_sorted.png")
print("cam", g.camera.x, g.camera.y)
