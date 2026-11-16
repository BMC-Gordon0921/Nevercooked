import os, sys
os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0, os.getcwd())
import pygame; pygame.init(); pygame.display.set_mode((1280,720))
from scenes.game import GameScene
from game.systems import render
class App:
    def switch(self,s): pass
g = GameScene(App()); w = g.world
print("bounds", w.bounds, "room", w.room)
bg, pos = render._background(w)
print("bg size", bg.get_size(), "pos", pos)
# world point (640, 190) -> bg local
bx, by = 640 - pos[0], 190 - pos[1]
print("bg at world(640,190):", bg.get_at((bx, by))[:3])
print("bg at world(640,300):", bg.get_at((640 - pos[0], 300 - pos[1]))[:3])
walls = [e for e in w.entities if e.height in (120, 44)]
print("wall count", len(walls))
for e in walls[:3]:
    print(e.sprite_key if hasattr(e,'sprite_key') else e, e.sprite.get_size(), e.sprite_rect(), e.foot)
