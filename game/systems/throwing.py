"""Q: throw whatever is in hand.

A throw is the same rules as pressing F, only at arm's length: if the tile in
front of the cook is a station that would accept the item, the item flies into
it and snaps home (load / add / serve / trash).  Otherwise it lands on the
floor -- on a free tile, never inside a machine.
"""
from __future__ import annotations

import pygame

from core import config
from game.entities.station import Station
from game.systems import interaction

TILES = config.TILE
SNATCH = 20          # how far past the tile edge a throw still counts as "at" a station


def landing(actor):
    """The patch of floor the item is aimed at, one and a half tiles ahead."""
    reach = int(TILES * config.TUNING["timing"]["throw_tiles"])
    fx, fy = actor.facing
    cx = actor.foot.centerx + fx * reach
    cy = actor.foot.bottom - 6 + fy * reach
    return pygame.Rect(cx - 12, cy - 12, 24, 24)


def _station_at(world, rect):
    """Nearest station the landing patch touches.  Reach is generous on purpose:
    the cook is aiming with a body, not a crosshair."""
    best = None
    best_dist = 1 << 30
    for station in world.stations:
        if not station.reach.inflate(SNATCH, SNATCH).colliderect(rect):
            continue
        dx = station.foot.centerx - rect.centerx
        dy = station.foot.centery - rect.centery
        dist = dx * dx + dy * dy
        if dist < best_dist:
            best, best_dist = station, dist
    return best


def _toss(world, actor, icon, to):
    world.tosses.append({
        "icon": icon,
        "x0": actor.foot.centerx,
        "y0": actor.foot.bottom - 40,
        "x1": to[0],
        "y1": to[1],
        "t": 0.0,
    })


def throw(world, actor):
    """Returns an event string for the feedback layer."""
    item = actor.hand
    if item is None:
        return "none"
    spot = landing(actor)
    station = _station_at(world, spot)

    if station is not None:
        before = actor.hand
        event, detail = interaction.interact_with_detail(world, actor, station)
        moved = actor.hand is not before or actor.hand is None
        if event not in ("none", "noop") and moved:
            _toss(world, actor, item.icon,
                  (station.foot.centerx, station.foot.top + 8))
            return event

    actor.hand = None
    _toss(world, actor, item.icon, (spot.centerx, spot.centery))
    world.drop_at(item, spot, actor)
    return "throw"
