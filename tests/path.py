"""Path and guidance contract: the route is contiguous, walkable, and ends
next to the machine the banner names."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from core.input import Intent
from game.systems import guide, nav
from scenes.game import GameScene

FAILS = []


def check(name, ok, info=""):
    print(("  ok   " if ok else "  FAIL ") + name + ((" | " + str(info)) if info else ""))
    if not ok:
        FAILS.append(name)


class FakeApp:
    running = True
    difficulty = "normal"

    def switch(self, scene):
        self.scene = scene


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    app = FakeApp()
    game = GameScene(app, "normal")
    world = game.world
    player = game.player
    grid = nav.grid_for(world)

    for _ in range(240):        # long enough for the first ticket (1.5s)
        game.update(1 / 60.0, Intent())

    step = game.guide
    check("guide present on an empty table", step is not None)
    check("guide has a stage mark", bool(step and step.get("mark")), step and step.get("mark"))
    check("guide has a counter", bool(step and step.get("total")), step and step.get("total"))

    station = step["station"]
    goal = nav.stand_for(world, player, station)
    check("stand cell found next to the goal", goal is not None, goal)
    route = nav.route(world, player, goal)
    check("route is not empty", bool(route), len(route or []))
    if route:
        start = grid.cell((player.foot.centerx, player.foot.centery))
        cells = [start] + route
        contiguous = all(abs(a[0] - b[0]) <= 1 and abs(a[1] - b[1]) <= 1
                         for a, b in zip(cells, cells[1:]))
        check("route steps are contiguous", contiguous)
        check("every route cell is walkable", all(grid.walkable(c) for c in route))
        check("route ends at the goal cell", route[-1] == goal, (route[-1], goal))

    check("game exposes the path", bool(game.path), len(game.path or []))
    check("game exposes the goal station", game.goal is station)

    # switching the path off in settings must not stop the arrow / banner
    game.show_path = False
    game._update_path(player)
    check("path cleared when toggled off", not game.path)
    check("goal still marked when toggled off", game.goal is station)

    # three dishes all produce a chain with a machine at the end
    for dish_id in config.DISHES:
        plan = guide.steps(dish_id)
        check("chain built for " + dish_id, bool(plan), [s["station"] for s in plan])
        check("chain ends on a station that exists",
              plan and any(s.stype == plan[-1]["station"] for s in world.stations))

    print("PATH:", "PASS" if not FAILS else "FAIL " + ", ".join(FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
