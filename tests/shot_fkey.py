"""Two frames that show the F-key fixes: the guard prompt and hand priority."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from core.input import Intent
from game.entities.item import GroundItem
from scenes.game import GameScene


class FakeApp:
    def __init__(self, level):
        self.running = True
        self.difficulty = level
        self.scene = None

    def switch(self, scene):
        self.scene = scene


def snap(surface, path):
    pygame.image.save(surface, os.path.join(os.path.dirname(__file__), path))
    print("saved", path)


def station(world, stype):
    return [s for s in world.stations if s.stype == stype][0]


def settle(scene, frames=12):
    for _ in range(frames):
        scene.update(1 / 60.0, Intent())
    return scene


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))

    # 1. hard mode: hands full, standing at the wok, facing away - F refuses
    app = FakeApp("hard")
    scene = GameScene(app, "hard")
    world, player = scene.world, scene.player
    wok = station(world, "wok")
    player.foot.center = (wok.reach.centerx, wok.reach.bottom + config.TILE // 2)
    player.hand = world.new_item("rice_steamed")
    player.hand.owner = player
    player.face(0, 1)
    scene.camera.center_on((player.foot.centerx, player.foot.bottom - 24))
    settle(scene)
    scene.draw(surface)
    snap(surface, "shot_fkey_guard.png")
    print("  label:", scene.label, "| detail:", repr(scene.detail))

    # 2. normal: rice in hand, egg on the floor at the feet, facing the wok
    app = FakeApp("normal")
    scene = GameScene(app, "normal")
    world, player = scene.world, scene.player
    wok = station(world, "wok")
    player.foot.center = (wok.reach.centerx, wok.reach.bottom + config.TILE // 2)
    egg = world.new_item("egg")
    world.drop_at(egg, pygame.Rect(player.foot.centerx, player.foot.centery, 1, 1), None)
    player.hand = world.new_item("rice_steamed")
    player.hand.owner = player
    player.face(0, -1)
    scene.camera.center_on((player.foot.centerx, player.foot.bottom - 24))
    settle(scene)
    scene.draw(surface)
    snap(surface, "shot_fkey_priority.png")
    print("  label:", scene.label, "| detail:", repr(scene.detail))


main()
