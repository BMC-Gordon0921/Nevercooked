"""Play a whole 180s round headless with random input: catches crashes and dead chains."""
import os
import random
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from core.input import Intent


class FakeApp:
    running = True

    def __init__(self):
        self.scene = None
        self.switched = []

    def switch(self, scene, **kwargs):
        self.scene = scene
        self.switched.append(type(scene).__name__)


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    from scenes.game import GameScene

    rng = random.Random(11)
    app = FakeApp()
    game = GameScene(app)
    world = game.world
    dt = 1.0 / 60.0
    keys = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]
    dx, dy = 0, 0
    frames = int(180.5 / dt)
    for i in range(frames):
        intent = Intent()
        if i % 14 == 0:
            dx, dy = rng.choice(keys)
        intent.mx, intent.my = dx, dy
        intent.sprint = rng.random() < 0.05
        intent.interact = rng.random() < 0.22
        intent.throw = rng.random() < 0.02
        game.update(dt, intent)
        game.draw(surface)
        if app.switched:
            break
    issues = world.validate()
    print("frames", i + 1, "switched", app.switched)
    score = world.score
    print("served", score.served, "failed", score.failed,
          "income", round(score.income, 1), "combo", score.best_combo)
    print("items alive", len(world.items), "stations holding",
          sum(1 for s in world.stations if s.slot is not None))
    print("validate", issues)
    return 0 if (not issues and app.switched) else 1


if __name__ == "__main__":
    sys.exit(main())
