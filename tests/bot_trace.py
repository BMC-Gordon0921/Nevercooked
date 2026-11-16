"""Trace the scripted player for a few seconds to see where time goes."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from core.input import Intent
from game.entities.station import Station
from game.systems import interaction
from scenes.game import GameScene

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bot import DT, FakeApp, Grid, cell_of, center_of, next_job, stations


def main():
    pygame.init()
    scene = GameScene(FakeApp())
    player = scene.player
    st = stations(scene)
    grid = Grid(scene.world)
    goal_cell, route = None, []
    last = None
    for frame in range(int(45 / DT)):
        it = Intent()
        job = next_job(st, player)
        if job is not None:
            want = grid.stand(job, player)
            here = cell_of(player.foot.center)
            if want != goal_cell or not route and here != want:
                goal_cell = want
                route = grid.path(here, want) or []
            if route and here != goal_cell:
                step = route[0]
                tx, ty = center_of(step)
                dx, dy = tx - player.foot.centerx, ty - player.foot.centery
                it.mx = (dx > 3) - (dx < -3)
                it.my = (dy > 3) - (dy < -3)
                if abs(dx) <= 3 and abs(dy) <= 3:
                    route.pop(0)
            else:
                route = []
            if not route:
                tx, ty = job.foot.centerx, job.foot.centery
                dx, dy = tx - player.foot.centerx, ty - player.foot.centery
                if abs(dx) > abs(dy):
                    it.mx = (dx > 0) - (dx < 0)
                else:
                    it.my = (dy > 0) - (dy < 0)
                it.interact = interaction.find_target(scene.world, player) is job
        scene.update(DT, it)
        hand = player.hand.item_id if player.hand else "-"
        sig = (job.stype if job else None, goal_cell, cell_of(player.foot.center), hand)
        if sig != last:
            last = sig
            wok, steamer = st["wok"], st["steamer"]
            print("%5.1fs job=%-9s goal=%s here=%s hand=%-12s steamer=%s/%s wok=%s/%s served=%d failed=%d"
                  % (frame * DT, sig[0], sig[1], sig[2], hand,
                     steamer.phase, [p for p in steamer.pending],
                     wok.phase, [p for p in wok.pending],
                     scene.world.score.served, scene.world.score.failed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
