"""Geometry guard: the cook targets the tile in front, and only that tile.

Two rules, both under test here:
  * strict aiming (challenge mode): the target is exactly the tile faced, so a
    diagonal position never reaches a machine that is merely nearby;
  * loose aiming (easier modes): facing the machine wins, but standing next to
    one is enough -- the tile is not a pixel-perfect hitbox.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from game.systems import difficulty, interaction
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


def strict(world, player, tune, inner, tile, failures):
    """Challenge mode: only the faced tile counts."""
    difficulty.set_level("hard")
    for station in world.stations:
        home = station.reach
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


def loose(world, player, tune, inner, tile, failures):
    """Easy/standard: beside a machine is enough, and facing beats proximity."""
    difficulty.set_level("normal")
    for station in world.stations:
        home = station.reach
        for dx, dy in CARDINALS:
            spot = pygame.Rect(home.x + dx * tile, home.y + dy * tile, tile, tile)
            if not inner.contains(spot):
                continue
            place(player, spot, tune, -dx, -dy)          # facing the machine
            found = interaction.find_target(world, player)
            if found is not station:
                failures.append("loose %s: facing it from %s hit %s"
                                % (station.stype, (dx, dy),
                                   getattr(found, "stype", found)))
            place(player, spot, tune, dx, dy)            # facing away from it
            found = interaction.find_target(world, player)
            if found is None:
                failures.append("loose %s: standing at %s facing away hit nothing"
                                % (station.stype, (dx, dy)))


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    world = World()
    player = world.player
    tune = config.TUNING["player"]
    inner = world.room.inflate(-config.TILE, -config.TILE)
    tile = config.TILE
    failures = []

    strict(world, player, tune, inner, tile, failures)
    loose(world, player, tune, inner, tile, failures)

    for line in failures:
        print("FAIL", line)
    print("stations=%d failures=%d" % (len(world.stations), len(failures)))
    print("REACH: " + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
