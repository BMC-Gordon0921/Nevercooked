"""Static configuration, loaded once from data/*.json."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
ART_DIR = os.path.join(ROOT, "assets", "art")
AUDIO_DIR = os.path.join(ROOT, "assets", "audio")

SCREEN_W, SCREEN_H = 1280, 720
BAR_TOP_H, BAR_BOTTOM_H = 40, 40
GAME_W = SCREEN_W
GAME_H = SCREEN_H - BAR_TOP_H - BAR_BOTTOM_H
GAME_TOP = BAR_TOP_H
TILE = 64


def load_json(name):
    with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


TUNING = load_json("tuning.json")
LAYOUT = load_json("layout.json")
PALETTE = load_json("palette.json")["names"]
_DISH_DOC = load_json("dishes.json")
DISH_LIST = _DISH_DOC["dishes"]
DISHES = {d["id"]: d for d in DISH_LIST}
TRANSFORMS = _DISH_DOC["transforms"]
RECIPES = _DISH_DOC["recipes"]
STATION_DEFS = {s["id"]: s for s in load_json("stations.json")["stations"]}
ITEMS = {i["id"]: i for i in load_json("ingredients.json")["items"]}


def hex_rgb(value):
    """'#RRGGBB' or '#RGB' to a 3-tuple."""
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def color(name, alpha=255):
    return (*hex_rgb(PALETTE[name]), alpha)
