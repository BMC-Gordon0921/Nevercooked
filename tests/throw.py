"""Throwing must be trustworthy: it either snaps into a machine or lands on
free floor -- never inside a counter, never gone."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from game.entities.item import GroundItem
from game.systems import difficulty, interaction
from game.world import World

TILE = config.TILE


def place(player, world, col, row, dx, dy):
    tile = world.tile_rect(col, row)
    tune = config.TUNING["player"]
    player.foot = pygame.Rect(0, 0, tune["foot_w"], tune["foot_h"])
    player.foot.center = tile.center
    player.target = None
    player.target_age = 0.0
    player.face(dx, dy)


def tile_of(world, entity):
    return ((entity.foot.centerx - world.room.x) // TILE,
            (entity.foot.centery - world.room.y) // TILE)


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    difficulty.set_level("easy")
    world = World()
    player = world.player
    problems = []

    steamer = next(s for s in world.stations if s.stype == "steamer")
    s_col, s_row = tile_of(world, steamer)

    # 1. a rice thrown at the steamer goes in, not on the floor
    world.give_to_hand(player, world.new_item("rice"))
    place(player, world, s_col, s_row + 1, 0, -1)
    event = interaction.throw(world, player)
    if steamer.slot is None or steamer.slot.item_id != "rice":
        problems.append("thrown rice did not land in the steamer (%r)" % event)
    if player.hand is not None:
        problems.append("hand still full after a successful throw")
    if not world.tosses:
        problems.append("no throw arc recorded")

    # 2. a dish thrown at a machine that will not take it lands on the floor
    before = len([e for e in world.entities if isinstance(e, GroundItem)])
    world.consume(steamer.slot)
    steamer.clear_slot()
    world.give_to_hand(player, world.new_item("fried_rice"))
    dish = player.hand
    place(player, world, s_col, s_row + 1, 0, -1)
    interaction.throw(world, player)
    after = len([e for e in world.entities if isinstance(e, GroundItem)])
    if after != before + 1:
        problems.append("refused throw did not produce a floor item (%d -> %d)"
                        % (before, after))
    if player.hand is not None:
        problems.append("hand still holds the refused dish")
    wrapper = next((e for e in world.entities
                    if isinstance(e, GroundItem) and e.item is dish), None)
    if wrapper is None:
        problems.append("refused dish is not on the floor at all")
    else:
        for station in world.stations:
            if station.foot.colliderect(wrapper.foot):
                problems.append("dish landed inside %s" % station.stype)

    # 3. empty aisle: throw forward, pick it back up with F
    place(player, world, 2, 2, 0, 1)
    item = world.new_item("egg")
    world.give_to_hand(player, item)
    interaction.throw(world, player)
    if player.hand is not None:
        problems.append("hand still full after an open-floor throw")
    want = world.tile_rect(2, 3)
    if not any(isinstance(e, GroundItem) and e.foot.colliderect(want)
               for e in world.entities):
        problems.append("egg did not land in the aimed tile")
    found = interaction.find_target(world, player)
    if not isinstance(found, GroundItem):
        problems.append("cannot see the thrown egg at all: %r" % (found,))
    else:
        event, _ = interaction.interact_with_detail(world, player, found)
        if player.hand is not item:
            problems.append("F did not pick the egg back up (%r)" % event)

    # 4. nothing vanished
    report = world.validate()
    if report:
        problems.append("validate: %r" % (report,))

    for line in problems:
        print("FAIL", line)
    print("THROW: " + ("PASS" if not problems else "FAIL"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
