"""Tile navigation shared by the guide path, the scripted bot and the AI brain.

Cells are room-relative: (0, 0) is the room's top-left tile, so they survive any
camera pan and any map swap.  Everything here is read-only with respect to the
world; the only cached state is the Grid itself, which is built from the solid
entity footprints (walls, blocks, stations) and never changes during a round.
"""
from __future__ import annotations

import heapq

import pygame

from core import config

TILE = config.TILE
DIR8 = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _room_xy(room):
    """The room accepts either the layout dict or a pygame.Rect."""
    if isinstance(room, dict):
        return room["x"], room["y"]
    return room.x, room.y


def cell_of(point, room=None):
    """World point -> room-relative tile."""
    room = room if room is not None else config.LAYOUT["room"]
    rx, ry = _room_xy(room)
    return int((point[0] - rx) // TILE), int((point[1] - ry) // TILE)


def center_of(cell, room=None):
    """Room-relative tile -> the world point at its centre."""
    room = room if room is not None else config.LAYOUT["room"]
    rx, ry = _room_xy(room)
    return rx + cell[0] * TILE + TILE // 2, ry + cell[1] * TILE + TILE // 2


def tile_rect(cell, room=None):
    room = room if room is not None else config.LAYOUT["room"]
    rx, ry = _room_xy(room)
    return pygame.Rect(rx + cell[0] * TILE, ry + cell[1] * TILE, TILE, TILE)


class Grid:
    """Eight-way A* over the room, with the player's own foot box as the probe."""

    def __init__(self, world):
        self.world = world
        self.room = world.room
        self.solid = [e.foot for e in world.entities if getattr(e, "solid", False)]
        self.w = self.room.width // TILE
        self.h = self.room.height // TILE
        self.foot_w = config.TUNING["player"]["foot_w"]
        self.foot_h = config.TUNING["player"]["foot_h"]
        self._walk = {}

    # -- geometry --------------------------------------------------------
    def cell(self, point):
        return cell_of(point, self.room)

    def center(self, cell):
        return center_of(cell, self.room)

    def rect(self, cell):
        return tile_rect(cell, self.room)

    def inside(self, cell):
        return 1 <= cell[0] < self.w - 1 and 1 <= cell[1] < self.h - 1

    def walkable(self, cell):
        cell = tuple(cell)
        hit = self._walk.get(cell)
        if hit is None:
            hit = self._probe(cell)
            self._walk[cell] = hit
        return hit

    def _probe(self, cell):
        if not self.inside(cell):
            return False
        cx, cy = self.center(cell)
        box = pygame.Rect(0, 0, self.foot_w, self.foot_h)
        box.center = (cx, cy)
        return not any(box.colliderect(s) for s in self.solid)

    # -- search ----------------------------------------------------------
    def path(self, start, goal):
        """Cells after `start` up to and including `goal`; None when unreachable."""
        start, goal = tuple(start), tuple(goal)
        if start == goal:
            return []
        openq = [(0, start)]
        cost = {start: 0.0}
        came = {}
        while openq:
            _, cur = heapq.heappop(openq)
            if cur == goal:
                out = [cur]
                while out[-1] in came:
                    out.append(came[out[-1]])
                return out[::-1][1:]
            for dx, dy in DIR8:
                nxt = (cur[0] + dx, cur[1] + dy)
                if not self.walkable(nxt):
                    continue
                if dx and dy and not (self.walkable((cur[0] + dx, cur[1])) and
                                      self.walkable((cur[0], cur[1] + dy))):
                    continue
                step = 1.4142 if dx and dy else 1.0
                new = cost[cur] + step
                if new < cost.get(nxt, 1e9):
                    cost[nxt] = new
                    came[nxt] = cur
                    h = abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1])
                    heapq.heappush(openq, (new + h, nxt))
        return None

    def nearest_walkable(self, cell):
        cell = tuple(cell)
        if self.walkable(cell):
            return cell
        for radius in range(1, 4):
            best, best_d = None, 1e9
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    cand = (cell[0] + dx, cell[1] + dy)
                    if self.walkable(cand):
                        d = abs(dx) + abs(dy)
                        if d < best_d:
                            best, best_d = cand, d
            if best:
                return best
        return None

    def stand(self, station, actor=None, prefer_from=None):
        """A walkable cardinal neighbour of `station`, closest to the actor."""
        sc = self.cell((station.foot.centerx, station.foot.centery))
        origin = None
        if prefer_from is not None:
            origin = tuple(prefer_from)
        elif actor is not None:
            origin = self.cell(actor.foot.center)
        best, best_d = None, 1e9
        for dx, dy in CARDINAL:
            cell = (sc[0] + dx, sc[1] + dy)
            if not self.walkable(cell):
                continue
            d = 0 if origin is None else abs(cell[0] - origin[0]) + abs(cell[1] - origin[1])
            if d < best_d:
                best, best_d = cell, d
        return best

    # -- steering --------------------------------------------------------
    def step_toward(self, actor, point, eps=3):
        """Unit input that walks the actor towards a world point."""
        dx = point[0] - actor.foot.centerx
        dy = point[1] - actor.foot.centery
        return (1 if dx > eps else -1 if dx < -eps else 0,
                1 if dy > eps else -1 if dy < -eps else 0)


def grid_for(world):
    """Cached Grid per world (solid entities never change mid-round)."""
    grid = getattr(world, "_nav_grid", None)
    if grid is None:
        grid = Grid(world)
        world._nav_grid = grid
    return grid


def route(world, actor, goal_cell):
    """Path from the actor's current cell to `goal_cell` (list of cells, no start)."""
    grid = grid_for(world)
    here = grid.cell(actor.foot.center)
    if here == tuple(goal_cell):
        return []
    return grid.path(here, tuple(goal_cell)) or []


def stand_for(world, actor, station):
    """The tile a cook should occupy to use `station` from where they stand."""
    return grid_for(world).stand(station, actor)
