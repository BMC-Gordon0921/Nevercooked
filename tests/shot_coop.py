"""Screenshots of the two-cook slice: HUD chip, settings rows, coop result."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config, profile
from core.input import Intent
from scenes.game import GameScene
from scenes.results import ResultsScene
from scenes.settings import SettingsScene


class FakeApp:
    def __init__(self, coop=False, profile_name="helper", policy="backlog"):
        self.running = True
        self.difficulty = "normal"
        self.scene = None
        self.coop = coop
        self.helper_profile = profile_name
        self.helper_policy = policy

    def switch(self, scene):
        self.scene = scene


def snap(surface, name):
    pygame.image.save(surface, os.path.join(os.path.dirname(__file__), name))
    print("saved", name)


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    saved = profile.load()
    profile.save_settings({"coop": True, "helper_profile": "helper",
                           "helper_policy": "backlog"})

    app = FakeApp(coop=True)
    game = GameScene(app, "normal")
    for _ in range(int(26 / (1 / 60.0))):
        game.update(1 / 60.0, Intent())
    game.draw(surface)
    print("helper job:", game.helper.state().get("job"), "| label:", game.helper.label())
    print("served:", len(game.world.orders.served),
          "helper missions:", len(game.helper.brain.missions))
    snap(surface, "shot_coop_game.png")

    game.helper.toggle()
    for _ in range(30):
        game.update(1 / 60.0, Intent())
    game.draw(surface)
    print("paused label:", game.helper.label())
    snap(surface, "shot_coop_paused.png")

    settings = SettingsScene(app, None)
    settings.draw(surface)
    snap(surface, "shot_coop_settings.png")

    settings.index = 3
    settings.draw(surface)
    snap(surface, "shot_coop_settings_coop.png")

    results = ResultsScene(app, game.world.score, "normal", coop=True)
    results.t = 1.0
    results.draw(surface)
    snap(surface, "shot_coop_results.png")

    profile.save(saved)
    return 0


if __name__ == "__main__":
    sys.exit(main())
