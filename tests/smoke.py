"""Headless smoke: import everything, run frames, screenshot, validate items."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config


class FakeApp:
    running = True

    def __init__(self):
        self.scene = None

    def switch(self, scene):
        self.scene = scene


def blank(**kw):
    from core.input import Intent
    it = Intent()
    for key, value in kw.items():
        setattr(it, key, value)
    return it


def main():
    pygame.init()
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    from scenes.game import GameScene

    app = FakeApp()
    scene = GameScene(app)
    assert scene.world.validate() == [], scene.world.validate()

    dt = 1.0 / 60.0
    for frame in range(240):
        scene.update(dt, blank())
        scene.draw(surface)
    pygame.image.save(surface, "tests/shot_idle.png")
    print("target after idle:", scene.target, repr(scene.label))
    print("orders", [o.name for o in scene.world.orders.active])
    print("validate", scene.world.validate())
    print("fps surface ok", surface.get_size())
    return 0


if __name__ == "__main__":
    sys.exit(main())
