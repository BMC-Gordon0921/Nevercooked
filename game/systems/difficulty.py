"""Difficulty levels: pacing, score multiplier, and which assists are on.

Why these tiers look like this (so future tuning does not re-derive it):
  mouse          the strongest assist - it removes walking and aiming entirely,
                 so standard drops it first.
  auto_free_hand keeps a full hand from dead-ending on a finished station; it is
                 a comfort feature, so normal keeps it and hard does not.
  loose_aim      stand anywhere next to a machine instead of one exact tile.
  swap           take the finished dish and put the held item back in one press.
  reason         the "this station wants X / you hold Y" line.
  aim/guide/dots/slot_hint/coach/tutorial  visual scaffolding only.

Hard keeps the feedback a player cannot play without: sound cues, progress bars,
ticket patience, and the target's name.
"""
from __future__ import annotations

from core import config

_DATA = config.load_json("difficulty.json")
ORDER = list(_DATA["order"])
DEFAULT = _DATA.get("default", "normal")
LEVELS = _DATA["levels"]

CODES = {str(k).strip().upper(): str(v)
         for k, v in (_DATA.get("codes") or {}).items() if str(k).strip()}

ACTIVE = DEFAULT


def set_level(level):
    global ACTIVE
    if level in LEVELS:
        ACTIVE = level
    return ACTIVE


def data(level=None):
    return LEVELS[level or ACTIVE]


def assist(name, level=None):
    """Is this assist enabled? Unknown keys default to on."""
    return bool(data(level)["assists"].get(name, True))


def patience_scale(level=None):
    return float(data(level)["patience"])


def spawn_scale(level=None):
    return float(data(level)["spawn"])


def score_scale(level=None):
    return float(data(level)["score"])


def codes():
    """Redemption codes defined in difficulty.json, upper-cased keys."""
    return dict(CODES)


def level_for_code(text):
    """Which level a redemption code opens, or None when it is not a code."""
    return CODES.get(str(text or "").strip().upper())
