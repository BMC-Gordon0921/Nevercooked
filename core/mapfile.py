"""Custom kitchen maps, authored as text.

A map is a JSON file with an ASCII floor plan and a legend, so a new layout is a
drawing problem, not a coding problem:

    "rows": ["########", "#r.e.*.#", "#..@...#", "########"]
    "#": wall   ".": floor   "@": spawn
    "r": crate of rice   "e": eggs   "*": stardust   ...  (any legend entry)

Why ASCII: a grid of numbers is unreadable in a diff and unreadable to whoever
is trying to picture the room.  A picture of the room is not.
"""
from __future__ import annotations

import json

KIND_WALL = "wall"
KIND_FLOOR = "floor"
KIND_CRATE = "crate"
KIND_STATION = "station"
KIND_SPAWN = "spawn"


class MapError(Exception):
    """The map file does not describe a playable kitchen."""


def _read(raw):
    if not isinstance(raw, dict):
        raise MapError("map must be a JSON object")
    rows = raw.get("rows")
    if not isinstance(rows, list) or not rows:
        raise MapError("map needs a non-empty 'rows' list of strings")
    width = len(rows[0])
    for index, line in enumerate(rows):
        if not isinstance(line, str):
            raise MapError("row %d is not a string" % index)
        if len(line) != width:
            raise MapError("row %d is %d wide, row 0 is %d"
                           % (index, len(line), width))
    legend = raw.get("legend")
    if not isinstance(legend, dict) or not legend:
        raise MapError("map needs a 'legend' object")
    return raw, rows, width, legend


def _entry(legend, char, row, col):
    value = legend.get(char)
    if value is None and char not in legend:
        raise MapError("row %d col %d: '%s' is not in the legend"
                       % (row, col, char))
    if not isinstance(value, dict):
        raise MapError("legend '%s' must be an object with a 'kind'" % char)
    kind = value.get("kind")
    if kind not in (KIND_WALL, KIND_FLOOR, KIND_CRATE, KIND_STATION, KIND_SPAWN):
        raise MapError("legend '%s' has unknown kind %r" % (char, kind))
    return value


def parse(raw):
    """Map document -> the layout dict the rest of the game already speaks."""
    raw, rows, width, legend = _read(raw)
    tile = int(raw.get("tile", 64))
    origin = raw.get("origin") or [96, 160]
    if not (isinstance(origin, list) and len(origin) == 2):
        raise MapError("'origin' must be [x, y]")
    height = len(rows)
    stations = []
    blocks = []
    spawn = None
    for row, line in enumerate(rows):
        for col, char in enumerate(line):
            entry = _entry(legend, char, row, col)
            kind = entry["kind"]
            if kind == KIND_WALL:
                if 0 < row < height - 1 and 0 < col < width - 1:
                    blocks.append([col, row])
            elif kind == KIND_SPAWN:
                spawn = [col, row]
            elif kind == KIND_CRATE:
                stations.append({"type": "crate", "tile": [col, row],
                                 "item": entry.get("item"),
                                 "label": entry.get("label")})
            elif kind == KIND_STATION:
                stations.append({"type": entry.get("type"), "tile": [col, row],
                                 "item": None, "label": entry.get("label")})
    if spawn is None:
        raise MapError("map has no spawn tile (legend entry with kind 'spawn')")
    if not stations:
        raise MapError("map has no stations")
    for entry in stations:
        if not entry["type"]:
            raise MapError("station at %r has no type" % (entry["tile"],))
    return {
        "grid": {"cols": width, "rows": height, "tile": tile},
        "room": {"x": int(origin[0]), "y": int(origin[1]),
                 "w": width * tile, "h": height * tile, "wall": tile},
        "spawn": spawn,
        "stations": stations,
        "blocks": blocks,
        "name": raw.get("name", ""),
    }


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except OSError as exc:
        raise MapError("cannot read %s: %s" % (path, exc))
    except ValueError as exc:
        raise MapError("%s is not valid JSON: %s" % (path, exc))
    return parse(raw)
