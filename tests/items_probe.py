import os, sys, random
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
from core import config
from core.input import Intent

class FakeApp:
    running = True
    def __init__(self): self.scene = None; self.switched = []
    def switch(self, scene, **k): self.scene = scene; self.switched.append(type(scene).__name__)

def main():
    pygame.init(); pygame.display.set_mode((1280, 720))
    from scenes.game import GameScene
    app = FakeApp(); game = GameScene(app); world = game.world
    created = {"n": 0}; consumed = {"n": 0}
    orig_new = world.new_item
    def new_item(iid):
        created["n"] += 1
        return orig_new(iid)
    world.new_item = new_item
    orig_consume = world.consume
    def consume(item):
        consumed["n"] += 1
        return orig_consume(item)
    world.consume = consume
    rng = random.Random(3); dt = 1/60
    keys = [(0,0),(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1)]
    dx = dy = 0
    for i in range(10800):
        it = Intent()
        if i % 14 == 0: dx, dy = rng.choice(keys)
        it.mx, it.my = dx, dy
        it.interact = rng.random() < 0.22
        it.throw = rng.random() < 0.02
        game.update(dt, it)
        if app.switched: break
    alive = len(world.items)
    print("created", created["n"], "consumed", consumed["n"], "alive", alive,
          "leak", created["n"] - consumed["n"] - alive)
    print("banked", getattr(world, "banked", {}))
    print("validate", world.validate())
    return 0
sys.exit(main())
