"""Screenshots for v0.3 guidance: floor path, step banner, settings screen."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from core.input import Intent
from scenes.game import GameScene
from scenes.settings import SettingsScene


class FakeApp:
    def __init__(self):
        self.running = True
        self.difficulty = "normal"
        self.scene = None

    def switch(self, scene):
        self.scene = scene


def snap(surface, name):
    pygame.image.save(surface, os.path.join(os.path.dirname(__file__), name))
    print("saved", name)


def cell_of(world, station):
    return ((station.foot.centerx - world.room.x) // config.TILE,
            (station.foot.centery - world.room.y) // config.TILE)


def stand(world, cell, dx, dy):
    player = world.player
    tune = config.TUNING["player"]
    player.foot = pygame.Rect(0, 0, tune["foot_w"], tune["foot_h"])
    player.foot.center = world.tile_rect(*cell).center
    player.face(dx, dy)


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    app = FakeApp()

    game = GameScene(app, "normal")
    for _ in range(240):
        game.update(1 / 60.0, Intent())
    crate = next(s for s in game.world.stations if s.stype == "crate")
    col, row = cell_of(game.world, crate)
    stand(game.world, (col, row + 1), 0, -1)
    press = Intent()
    press.interact = True
    game.update(1 / 60.0, press)
    for _ in range(20):
        game.update(1 / 60.0, Intent())
    stand(game.world, (col + 3, row + 3), 0, -1)
    for _ in range(6):
        game.update(1 / 60.0, Intent())
    game.draw(surface)
    snap(surface, "shot_v3_path.png")
    print("guide:", game.guide)
    print("path cells:", len(game.path or []))

    settings = SettingsScene(app, None)
    settings.draw(surface)
    snap(surface, "shot_v3_settings.png")

    settings.index = 2
    settings.draw(surface)
    snap(surface, "shot_v3_settings_path.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
