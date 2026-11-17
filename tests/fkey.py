"""The two interaction faults from the playtest, pinned down.

1. In hard mode F used to *drop* the held ingredient when the chef stood at a
   counter but was not facing that exact tile - the item fell on the floor
   "outside the station" and was gone.
2. With both hands full, a loose item on the floor could steal the target from
   the station right in front of the chef, so the rice went on the ground and
   the egg got picked up instead.
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
pygame.display.set_mode((320, 240))

from core import config
from game.entities.item import GroundItem
from game.systems import difficulty, interaction
from game.world import World
from tests.layout import open_aisle

FAIL = []


def check(name, ok, info=""):
    print(("  ok   " if ok else "  FAIL ") + name + ("  " + str(info) if info != "" else ""))
    if not ok:
        FAIL.append(name)


def station(world, stype):
    return [s for s in world.stations if s.stype == stype][0]


def fresh(level, facing, hand_id=None, stype=None):
    world = World()
    player = world.player
    difficulty.set_level(level)
    if stype is not None:
        spot = station(world, stype)
        player.foot.center = (spot.reach.centerx, spot.reach.bottom + config.TILE // 2)
    player.face(*facing)
    if hand_id:
        player.hand = world.new_item(hand_id)
        player.hand.owner = player
    player.target = None
    player.target_age = 0.0
    return world, player


def press(world, player):
    target = interaction.resolve(player, world)
    label, detail = interaction.explain(player, target, world)
    event, info = interaction.interact_with_detail(world, player, target)
    return event, label, detail, target


def loose(world):
    return [e for e in world.entities if isinstance(e, GroundItem) and e.alive]


print("A. hard mode, full hands, standing at the wok but facing away")
world, player = fresh("hard", (0, 1), "rice_steamed", "wok")
event, label, detail, _ = press(world, player)
check("F does not drop the ingredient", event != "drop" and player.hand is not None, event)
check("nothing lands on the floor", not loose(world))
check("the prompt names the counter to face", "灶台" in label, label)

print("B. hard mode, same spot, actually facing the wok")
world, player = fresh("hard", (0, -1), "rice_steamed", "wok")
wok = station(world, "wok")
event, _, _, _ = press(world, player)
check("F loads the rice", event == "load", event)
check("the wok holds the rice", getattr(wok.slot, "item_id", None) == "rice_steamed")

print("C. normal, rice in hand, egg on the floor underfoot, facing the wok")
world, player = fresh("normal", (0, -1), "rice_steamed", "wok")
wok = station(world, "wok")
egg = world.new_item("egg")
world.drop_at(egg, pygame.Rect(player.foot.centerx, player.foot.centery, 1, 1), None)
event, _, _, target = press(world, player)
check("the wok wins over the egg underfoot", event == "load" and target is wok, event)
check("the rice went in", getattr(wok.slot, "item_id", None) == "rice_steamed")
check("the egg stays on the floor", len(loose(world)) == 1)

print("D. empty hands, egg underfoot, facing away from the counter")
world, player = fresh("normal", (0, 1), None, "wok")
egg = world.new_item("egg")
world.drop_at(egg, pygame.Rect(player.foot.centerx, player.foot.centery, 1, 1), None)
event, _, _, _ = press(world, player)
check("F picks the egg up", event == "pickup" and getattr(player.hand, "item_id", None) == "egg", event)

print("E. hard mode, full hands, open floor: dropping still works")
world, player = fresh("hard", (0, 1), "rice")
cell, (dx, dy), _ahead = open_aisle(world)
player.foot.center = world.tile_rect(*cell).center
player.face(dx, dy)
cook = player.foot.center
event, _, _, _ = press(world, player)
drops = loose(world)
check("F drops the rice", event == "drop" and player.hand is None, event)
check("it lands in front of the sprite",
      bool(drops) and ((drops[0].foot.centerx - cook[0]) * dx
                       + (drops[0].foot.centery - cook[1]) * dy) > 0,
      [tuple(g.foot.center) for g in drops])
check("it lands where it can be reached again", bool(drops) and world.spot_is_free(drops[0].foot))

print("F. hard mode, full hands, facing the bin: still trashes")
world, player = fresh("hard", (0, -1), "rice", "trash")
event, _, _, _ = press(world, player)
check("the bin takes it", event == "trash" and player.hand is None, event)

print()
if FAIL:
    print("FKEY: FAIL (%d)" % len(FAIL))
    sys.exit(1)
print("FKEY: PASS")
