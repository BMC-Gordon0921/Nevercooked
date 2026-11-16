"""Render the current map to tests/map_preview.png.

The map loader checks shape, not reachability; this picture is how a human
checks that the cook can actually walk to every machine.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import assets, config, text as textmod
from game.world import World

ZOOM = 2


def scaled(surface, zoom):
    return pygame.transform.scale(surface, (surface.get_width() * zoom,
                                            surface.get_height() * zoom))


def main():
    pygame.init()
    pygame.display.set_mode((320, 240))
    world = World()
    room = world.room
    tile = config.TILE
    plate = pygame.Surface((room.w * ZOOM, room.h * ZOOM))
    floor_a = scaled(assets.image("floor_a", (tile, tile)), ZOOM)
    floor_b = scaled(assets.image("floor_b", (tile, tile)), ZOOM)
    cols = room.w // tile
    rows = room.h // tile
    for row in range(rows):
        for col in range(cols):
            plate.blit(floor_a if (col + row) % 2 == 0 else floor_b,
                       (col * tile * ZOOM, row * tile * ZOOM))
    for station in world.stations:
        sprite = station.sprite
        if sprite is None:
            continue
        big = scaled(sprite, ZOOM)
        rect = station.foot
        pos = ((rect.centerx - room.x) * ZOOM - big.get_width() // 2,
               (rect.bottom - room.y) * ZOOM - big.get_height())
        plate.blit(big, pos)
        label = textmod.render(station.label, 12, (40, 44, 56))
        plate.blit(label, label.get_rect(midtop=(
            (rect.centerx - room.x) * ZOOM, (rect.bottom - room.y) * ZOOM + 2)))
    spawn = world.tile_rect(*config.LAYOUT["spawn"])
    pygame.draw.rect(plate, (56, 225, 255),
                     ((spawn.x - room.x) * ZOOM + 6, (spawn.y - room.y) * ZOOM + 6,
                      spawn.w * ZOOM - 12, spawn.h * ZOOM - 12), 3)
    pygame.draw.rect(plate, (60, 70, 90), (0, 0, room.w * ZOOM, room.h * ZOOM), 3)
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests",
                                        "map_preview.png"))
    pygame.image.save(plate, path)
    print("saved tests/map_preview.png  %dx%d" % plate.get_size())
    print("name:", config.LAYOUT.get("name", ""), "stations:", len(world.stations))
    return 0


if __name__ == "__main__":
    sys.exit(main())
