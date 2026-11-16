"""Geometry guard: the chef targets the tile in front, and only that tile.

Regression test for "standing between two machines grabs the wrong one".
Rule under test (game/systems/interaction.py:probe_rect):
  * the probe is exactly one tile -- the tile the chef faces;
  * a diagonal position never reaches anything the chef is not facing;
  * standing beside a machine always targets that machine.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from game.systems import interaction
from game.world import World

CARDINALS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def place(player, spot, tune, dx, dy):
    player.foot = pygame.Rect(0, 0, tune["foot_w"], tune["foot_h"])
    player.foot.center = spot.center
    player.target = None
    player.target_age = 0.0
    player.face(dx, dy)


def station_at(world, rect):
    for station in world.stations:
        if station.reach.colliderect(rect):
            return station
    return None


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    world = World()
    player = world.player
    tune = config.TUNING["player"]
    inner = world.room.inflate(-config.TILE, -config.TILE)
    tile = config.TILE
    failures = []

    for station in world.stations:
        home = station.reach
        # 1. beside it, facing it -> it
        for dx, dy in CARDINALS:
            spot = pygame.Rect(home.x + dx * tile, home.y + dy * tile, tile, tile)
            if not inner.contains(spot):
                continue
            place(player, spot, tune, -dx, -dy)
            found = interaction.find_target(world, player)
            if found is not station:
                failures.append("%s: beside %s facing back hit %s"
                                % (station.stype, (dx, dy),
                                   getattr(found, "stype", found)))
        # 2. diagonal to it, facing any cardinal -> only what that tile holds
        for dx in (-1, 1):
            for dy in (-1, 1):
                spot = pygame.Rect(home.x + dx * tile, home.y + dy * tile, tile, tile)
                if not inner.contains(spot):
                    continue
                for fx, fy in CARDINALS:
                    place(player, spot, tune, fx, fy)
                    found = interaction.find_target(world, player)
                    want = station_at(
                        world,
                        pygame.Rect(spot.x + fx * tile, spot.y + fy * tile, tile, tile))
                    if found is not want:
                        failures.append(
                            "%s: diagonal %s facing %s hit %s, wanted %s"
                            % (station.stype, (dx, dy), (fx, fy),
                               getattr(found, "stype", found),
                               getattr(want, "stype", want)))

    for line in failures:
        print("FAIL", line)
    print("stations=%d failures=%d" % (len(world.stations), len(failures)))
    print("REACH: " + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
