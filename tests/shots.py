"""Render every screen to a PNG so the whole flow can be eyeballed."""
import os
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

    def switch(self, scene):
        self.scene = scene


def empty():
    return Intent()


def main():
    pygame.init()
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    from scenes.title import TitleScene
    from scenes.game import GameScene
    from scenes.results import ResultsScene

    app = FakeApp()

    title = TitleScene(app)
    for _ in range(30):
        title.update(1 / 60.0, empty())
    title.draw(surface)
    pygame.image.save(surface, "tests/shot_title.png")

    game = GameScene(app)
    world = game.world
    crate = [s for s in world.stations if s.dispense == "rice"][0]
    steamer = [s for s in world.stations if s.stype == "steamer"][0]
    wok = [s for s in world.stations if s.stype == "wok"][0]
    world.give_to_hand(game.player, world.new_item("stardust"))
    world.feed(steamer, world.new_item("rice"))
    steamer.phase = "cook"
    steamer.duration = 10.0
    steamer.timer = 6.4
    world.feed(wok, world.new_item("rice_steamed"))
    wok.phase = "add"
    wok.pending = ["egg"]
    game.player.foot.center = (wok.foot.centerx, wok.foot.bottom + 40)
    for _ in range(420):
        game.update(1 / 60.0, empty())
    game.draw(surface)
    pygame.image.save(surface, "tests/shot_play.png")

    game.player.foot.center = (wok.foot.centerx, wok.foot.bottom - 26)
    game.player.busy = 0.2
    game.player.busy_total = 0.35
    for _ in range(12):
        game.update(1 / 60.0, empty())
    game.draw(surface)
    pygame.image.save(surface, "tests/shot_occlusion.png")

    game.paused = True
    game.draw(surface)
    pygame.image.save(surface, "tests/shot_pause.png")
    game.paused = False

    from game.systems.scoring import ScoreBoard
    score = ScoreBoard()
    score.income = 486
    score.tips = 58
    score.served = 17
    score.failed = 3
    score.best_combo = 9
    score.burnt_trashed = 2
    results = ResultsScene(app, score)
    results.t = 1.0
    results.draw(surface)
    pygame.image.save(surface, "tests/shot_results.png")
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
