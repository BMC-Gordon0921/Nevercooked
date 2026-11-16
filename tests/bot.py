"""How many orders can one focused player actually serve? A scripted customer.

Drives the real GameScene with a greedy fried-rice worker that walks a tile grid
(A*), so detours around the machines count. Reports served vs offered per speed.
"""
import heapq
import os
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config
from game.entities.station import Station
from core.input import Intent
from game.systems import interaction
from scenes.game import GameScene

DT = 1.0 / 60.0
TILE = config.TILE


class FakeApp:
    running = True

    def __init__(self):
        self.scene = None

    def switch(self, scene):
        self.scene = scene


ROOM = config.LAYOUT["room"]


def cell_of(point):
    """Screen point -> room-relative tile (0,0 is the room's top-left tile)."""
    return int((point[0] - ROOM["x"]) // TILE), int((point[1] - ROOM["y"]) // TILE)


def center_of(cell):
    return (ROOM["x"] + cell[0] * TILE + TILE // 2, ROOM["y"] + cell[1] * TILE + TILE // 2)


class Grid:
    def __init__(self, world):
        self.world = world
        self.solid = [e.foot for e in world.entities if getattr(e, "solid", False)]
        self.tx0 = 0
        self.ty0 = 0
        self.w = world.room.width // TILE
        self.h = world.room.height // TILE

    def walkable(self, cell):
        tx, ty = cell
        if not (self.tx0 + 1 <= tx < self.tx0 + self.w - 1):
            return False
        if not (self.ty0 + 1 <= ty < self.ty0 + self.h - 1):
            return False
        cx, cy = center_of(cell)
        probe = pygame.Rect(0, 0, config.TUNING["player"]["foot_w"],
                            config.TUNING["player"]["foot_h"])
        probe.center = (cx, cy)
        return not any(probe.colliderect(s) for s in self.solid)

    def path(self, start, goal):
        if start == goal:
            return []
        openq = [(0, start)]
        cost = {start: 0}
        came = {}
        while openq:
            _, cur = heapq.heappop(openq)
            if cur == goal:
                out = [cur]
                while out[-1] in came:
                    out.append(came[out[-1]])
                return out[::-1][1:]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nxt = (cur[0] + dx, cur[1] + dy)
                step = 1.41 if dx and dy else 1.0
                if dx and dy and not (self.walkable((cur[0] + dx, cur[1])) and
                                      self.walkable((cur[0], cur[1] + dy))):
                    continue
                if not self.walkable(nxt):
                    continue
                new = cost[cur] + step
                if new < cost.get(nxt, 1e9):
                    cost[nxt] = new
                    came[nxt] = cur
                    heapq.heappush(openq, (new + abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1]), nxt))
        return None

    def stand(self, station, player):
        """A walkable cell next to the station, closest to where we are now."""
        sc = cell_of((station.foot.centerx, station.foot.centery))
        here = cell_of(player.foot.center)
        best, best_d = None, 1e9
        # Cardinal neighbours only: the interaction probe sits one tile ahead,
        # so diagonals can never reach a machine.
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cell = (sc[0] + dx, sc[1] + dy)
                if not self.walkable(cell):
                    continue
                d = abs(cell[0] - here[0]) + abs(cell[1] - here[1])
                if d < best_d:
                    best, best_d = cell, d
        return best or sc


def stations(scene):
    out = {}
    for s in scene.world.stations:
        out[s.dispense or s.stype] = s
    return out


def next_job(st, player):
    hand = player.hand.item_id if player.hand else None
    wok, steamer = st["wok"], st["steamer"]
    if hand in ("egg", "stardust"):
        return wok
    if hand == "fried_rice":
        return st["serve"]
    if hand == "rice":
        return steamer
    if hand == "rice_steamed":
        return wok if wok.phase == Station.PHASE_IDLE else None
    if wok.phase == Station.PHASE_READY:
        return wok
    if wok.phase == Station.PHASE_ADD and wok.pending:
        return st[wok.pending[0]]
    if steamer.phase == Station.PHASE_READY:
        return steamer
    if steamer.phase == Station.PHASE_IDLE:
        return st["rice"]
    return None


def run(speed, label, seconds=180.0, film=None):
    config.TUNING["player"]["speed"] = speed
    scene = GameScene(FakeApp())
    player = scene.player
    st = stations(scene)
    grid = Grid(scene.world)
    goal_cell, route = None, []
    idle = 0.0
    frames = 0
    next_shot = 0.0
    for _ in range(int(seconds / DT)):
        if not isinstance(scene, GameScene):
            break
        frames += 1
        it = Intent()
        job = next_job(st, player)
        if job is None:
            idle += DT
        else:
            want = grid.stand(job, player)
            here = cell_of(player.foot.center)
            if want != goal_cell or not route and here != want:
                goal_cell = want
                route = grid.path(here, want) or []
            # keep the route fresh as we walk
            if route and cell_of(player.foot.center) != goal_cell:
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
                # in place: face the station and press
                tx, ty = job.foot.centerx, job.foot.centery
                dx, dy = tx - player.foot.centerx, ty - player.foot.centery
                if abs(dx) > abs(dy):
                    it.mx = (dx > 0) - (dx < 0)
                else:
                    it.my = (dy > 0) - (dy < 0)
                it.interact = interaction.find_target(scene.world, player) is job
        scene.update(DT, it)
        if film is not None and scene.elapsed >= next_shot:
            canvas = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
            scene.draw(canvas)
            pygame.image.save(canvas, os.path.join(film, "film_%03d.png" % int(scene.elapsed)))
            next_shot += 20.0

    world = scene.world
    score = world.score
    offered = score.served + score.failed + len(world.orders.active) + len(world.orders.queue)
    print("%-6s speed=%3d served=%2d failed=%2d offered=%2d idle=%4.1fs stars=%4d coins=%3d"
          % (label, speed, score.served, score.failed, offered, idle,
             score.final_stars(), score.coins()))
    return score


def main():
    pygame.init()
    for speed in (112, 160, 200):
        run(speed, "walk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
