"""Map file: a good map loads, a broken map is refused, and interior walls block."""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import config, mapfile
from game.world import World

GOOD = {
    "name": "test",
    "tile": 64,
    "origin": [64, 128],
    "legend": {
        "#": {"kind": "wall"},
        ".": {"kind": "floor"},
        "@": {"kind": "spawn"},
        "r": {"kind": "crate", "item": "rice", "label": "米箱"},
        "S": {"kind": "station", "type": "steamer", "label": "蒸笼"},
        "P": {"kind": "station", "type": "serve", "label": "出餐口"},
    },
    "rows": ["#####", "#r.S#", "#.@.#", "#..P#", "#####"],
}


def expect_error(raw, why, problems):
    try:
        mapfile.parse(raw)
    except mapfile.MapError:
        return
    problems.append("accepted a bad map: " + why)


def main():
    pygame.init()
    pygame.display.set_mode((320, 240))
    problems = []

    # 1. the shipped map loads and is playable
    if config.MAP_ERROR:
        problems.append("shipped map failed: %s" % config.MAP_ERROR)
    layout = config.LAYOUT
    types = [s["type"] for s in layout["stations"]]
    if len(types) != 13:
        problems.append("default map has %d stations, expected 13" % len(types))
    for needed in ("crate", "steamer", "wok", "oven", "board", "assemble",
                   "serve", "trash"):
        if needed not in types:
            problems.append("default map is missing a %s" % needed)
    cols, rows = layout["grid"]["cols"], layout["grid"]["rows"]
    spawn = layout["spawn"]
    if not (0 < spawn[0] < cols - 1 and 0 < spawn[1] < rows - 1):
        problems.append("spawn %r is inside a wall" % (spawn,))

    # 2. a custom map parses to the same shape the game speaks
    custom = mapfile.parse(GOOD)
    if custom["room"]["w"] != 5 * 64 or custom["room"]["h"] != 5 * 64:
        problems.append("custom room size wrong: %r" % (custom["room"],))
    if custom["spawn"] != [2, 2]:
        problems.append("custom spawn wrong: %r" % (custom["spawn"],))
    if len(custom["stations"]) != 3:
        problems.append("custom stations wrong: %r" % (custom["stations"],))

    # 3. broken maps are refused instead of half-loaded
    ragged = dict(GOOD, rows=["#####", "#r.S#", "#.@.#", "#..P", "#####"])
    expect_error(ragged, "ragged rows", problems)
    unknown = dict(GOOD, rows=["#####", "#r.X#", "#.@.#", "#..P#", "#####"])
    expect_error(unknown, "character outside legend", problems)
    no_spawn = dict(GOOD, rows=["#####", "#r.S#", "#...#", "#..P#", "#####"])
    expect_error(no_spawn, "no spawn", problems)
    no_station = dict(GOOD, rows=["#####", "#...#", "#.@.#", "#...#", "#####"])
    expect_error(no_station, "no stations", problems)
    bad_kind = dict(GOOD, legend=dict(GOOD["legend"], r={"kind": "sink"}))
    expect_error(bad_kind, "unknown kind", problems)

    # 4. an interior wall becomes a solid body
    world = World()
    world2 = World.__new__(World)
    world2.room = pygame.Rect(0, 0, 5 * 64, 5 * 64)
    walled = mapfile.parse(dict(GOOD, rows=["#####", "#r#S#", "#.@.#", "#..P#", "#####"]))
    if walled["blocks"] != [[2, 1]]:
        problems.append("interior wall not reported: %r" % (walled["blocks"],))
    if not any(e.solid for e in world.entities if e.foot.w == 64):
        problems.append("world has no solid wall tiles")

    # 5. map.json and map_default.json describe the same kitchen
    here = os.path.join(config.DATA_DIR)
    with open(os.path.join(here, "map.json"), encoding="utf-8") as fh:
        live = mapfile.parse(json.load(fh))
    with open(os.path.join(here, "map_default.json"), encoding="utf-8") as fh:
        default = mapfile.parse(json.load(fh))
    if live != default:
        problems.append("map.json and map_default.json disagree")

    for line in problems:
        print("FAIL", line)
    print("MAP: " + ("PASS" if not problems else "FAIL"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
