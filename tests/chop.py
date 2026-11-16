"""Chopping must finish on a single F press: no meter, no busy lock."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core.input import Intent
from scenes.game import GameScene

DT = 1.0 / 60.0


class FakeApp:
    running = True

    def __init__(self):
        self.scene = None

    def switch(self, scene):
        self.scene = scene


def press(scene, interact=False):
    it = Intent()
    it.interact = interact
    scene.update(DT, it)


def stand_below(scene, station):
    player = scene.player
    player.foot.center = (station.foot.centerx, station.foot.bottom + 14)
    player.facing = (0, -1)
    player.facing_index = 1
    player.target = None
    player.target_age = 0.0


def main():
    pygame.init()
    app = FakeApp()
    scene = GameScene(app)
    player = scene.player
    board = [s for s in scene.world.stations if s.stype == "board"][0]
    crate = [s for s in scene.world.stations if s.dispense == "meat"][0]

    stand_below(scene, crate)
    press(scene, interact=True)
    assert player.hand is not None and player.hand.item_id == "meat", player.hand

    stand_below(scene, board)
    press(scene, interact=True)
    assert board.slot is not None and board.slot.item_id == "meat", "meat not on board"

    press(scene, interact=True)  # one press
    assert board.slot is not None, "board lost its item"
    print("after one press: slot=", board.slot.item_id, "phase=", board.phase,
          "busy=", round(player.busy, 2))
    assert board.slot.item_id == "meat_cut", "chop did not finish in one press"
    assert player.busy == 0.0, "chop must not lock the player"

    press(scene, interact=True)
    assert player.hand is not None and player.hand.item_id == "meat_cut"
    print("took back:", player.hand.item_id)
    scene.world.consume(player.hand)  # sanctioned destroy point, frees the hands
    player.hand = None

    veg_board = board
    veg = [s for s in scene.world.stations if s.dispense == "veg"][0]
    stand_below(scene, veg)
    press(scene, interact=True)
    stand_below(scene, veg_board)
    press(scene, interact=True)
    press(scene, interact=True)
    assert veg_board.slot.item_id == "veg_cut", veg_board.slot.item_id
    print("veg chop ok:", veg_board.slot.item_id)

    print("validate:", scene.world.validate())
    assert scene.world.validate() == []
    print("CHOP INSTANT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
