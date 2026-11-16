"""Drive the whole fried-rice chain through the real interaction layer."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from core.input import Intent
from scenes.game import GameScene

DT = 1.0 / 60.0


class FakeApp:
    running = True

    def __init__(self):
        self.scene = None

    def switch(self, scene):
        self.scene = scene


def press(scene, interact=False, throw=False):
    it = Intent()
    it.interact = interact
    it.throw = throw
    scene.update(DT, it)


def stand_below(scene, station):
    player = scene.player
    player.foot.center = (station.foot.centerx, station.foot.bottom + 14)
    player.facing = (0, -1)
    player.facing_index = 1
    player.target = None
    player.target_age = 0.0


def use(scene, station, times=1):
    for _ in range(times):
        stand_below(scene, station)
        press(scene, interact=True)


def wait(scene, seconds):
    steps = int(seconds / DT)
    for _ in range(steps):
        press(scene)


def find(scene, stype):
    for station in scene.world.stations:
        if station.stype == stype:
            return station
    raise KeyError(stype)


def main():
    pygame.init()
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    app = FakeApp()
    scene = GameScene(app)
    player = scene.player

    crate_rice = [s for s in scene.world.stations if s.dispense == "rice"][0]
    crate_egg = [s for s in scene.world.stations if s.dispense == "egg"][0]
    crate_dust = [s for s in scene.world.stations if s.dispense == "stardust"][0]
    steamer = find(scene, "steamer")
    wok = find(scene, "wok")
    serve = find(scene, "serve")

    use(scene, crate_rice)
    print("1 hand:", player.hand)
    use(scene, steamer)
    print("2 steamer phase:", steamer.phase, "slot:", steamer.slot)
    wait(scene, 10.4)
    print("3 steamer phase:", steamer.phase, "slot:", steamer.slot)
    use(scene, steamer)
    print("4 hand:", player.hand)

    use(scene, wok)
    print("5 wok phase:", wok.phase, "pending:", wok.pending)
    use(scene, crate_egg)
    use(scene, wok)
    print("6 pending:", wok.pending)
    use(scene, crate_dust)
    use(scene, wok)
    print("7 phase:", wok.phase, "dur:", wok.duration)
    wait(scene, 8.4)
    print("8 phase:", wok.phase, "slot:", wok.slot)
    use(scene, wok)
    print("9 hand:", player.hand, "quality:", player.hand.quality if player.hand else None)

    print("10 orders:", [(o.name, round(o.time_left, 1)) for o in scene.world.orders.active])
    use(scene, serve)
    score = scene.world.score
    print("11 served:", score.served, "income:", score.income, "combo:", score.combo,
          "last:", score.last)
    print("12 validate:", scene.world.validate())
    print("13 stars:", score.final_stars(), "coins:", score.coins())
    scene.draw(surface)
    pygame.image.save(surface, "tests/shot_served.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
