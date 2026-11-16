"""Screenshots for eyeballing the v0.2 UI: title, first shift, guidance."""
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
from scenes.title import TitleScene


class FakeApp:
    def __init__(self):
        self.running = True
        self.difficulty = "normal"
        self.scene = None

    def switch(self, scene):
        self.scene = scene


def snap(surface, path):
    pygame.image.save(surface, os.path.join(os.path.dirname(__file__), path))
    print("saved", path)


def tile(world, col, row):
    return world.tile_rect(col, row)


def stand(world, col, row, dx, dy):
    player = world.player
    tune = config.TUNING["player"]
    player.foot = pygame.Rect(0, 0, tune["foot_w"], tune["foot_h"])
    player.foot.center = tile(world, col, row).center
    player.face(dx, dy)


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    app = FakeApp()

    title = TitleScene(app)
    for _ in range(30):
        title.update(1 / 60.0, Intent())
    title.draw(surface)
    snap(surface, "shot_v2_title.png")

    game = GameScene(app, "normal")
    for _ in range(40):
        game.update(1 / 60.0, Intent())
    crate = next(s for s in game.world.stations if s.stype == "crate")
    s_col = (crate.foot.centerx - game.world.room.x) // config.TILE
    s_row = (crate.foot.centery - game.world.room.y) // config.TILE
    stand(game.world, s_col, s_row + 1, 0, -1)
    again = Intent()
    again.interact = True
    game.update(1 / 60.0, again)
    for _ in range(30):
        game.update(1 / 60.0, Intent())
    game.draw(surface)
    snap(surface, "shot_v2_play.png")

    steamer = next(s for s in game.world.stations if s.stype == "steamer")
    st_col = (steamer.foot.centerx - game.world.room.x) // config.TILE
    st_row = (steamer.foot.centery - game.world.room.y) // config.TILE
    stand(game.world, st_col, st_row + 1, 0, -1)
    press = Intent()
    press.interact = True
    game.update(1 / 60.0, press)
    for _ in range(120):
        game.update(1 / 60.0, Intent())
    game.draw(surface)
    snap(surface, "shot_v2_cooking.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
