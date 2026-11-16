import os, sys
os.environ['SDL_VIDEODRIVER']='dummy'; os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0, os.getcwd())
import pygame; pygame.init(); pygame.display.set_mode((1280,720))
from core import config
from game.world import World
from game.systems.camera import Camera
w = World()
print("room", w.room, "bounds", w.bounds)
print("view", 1280//2, 640//2)
for s in w.stations:
    print(s.stype, "tile-rect", tuple(s.reach), "sprite-h", s.height if hasattr(s,'height') else '?')
p = w.player
cam = Camera(zoom=2); cam.set_bounds(w.bounds)
cam.center_on((p.foot.centerx, p.foot.bottom - 24))
print("player foot", tuple(p.foot))
print("cam left/top", cam.left, cam.top, "size", cam.world_w, cam.world_h)
