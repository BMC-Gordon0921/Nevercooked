"""Layout helpers for the interaction tests.

The tests used to hardcode "tile (2,2) is an empty aisle" and broke the moment
the kitchen was redrawn. Anything that depends on the map shape goes here.
"""
from __future__ import annotations

from core import config
from game.systems import nav

DIRS = ((0, 1), (0, -1), (1, 0), (-1, 0))


def open_aisle(world):
    """A walkable tile whose forward neighbour is also open floor.

    Returns (cell, (dx, dy), next_cell) with no station reach touching either
    tile, so a dropped or thrown item cannot end up on a counter.
    """
    grid = nav.grid_for(world)
    cols = world.room.w // config.TILE
    rows = world.room.h // config.TILE
    for row in range(1, rows - 1):
        for col in range(1, cols - 1):
            cell = (col, row)
            if not grid.walkable(cell):
                continue
            here = world.tile_rect(col, row)
            if any(st.reach.colliderect(here) for st in world.stations):
                continue
            for dx, dy in DIRS:
                nxt = (col + dx, row + dy)
                if not grid.walkable(nxt):
                    continue
                ahead = world.tile_rect(*nxt)
                if any(st.reach.colliderect(ahead) for st in world.stations):
                    continue
                return cell, (dx, dy), nxt
    return None, None, None
