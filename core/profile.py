"""What this cook has unlocked, and how they like to hear the kitchen.

One small JSON in the project root: best stars per level, which levels are open,
and the settings (sfx volume, music volume, whether the ground arrow path is
drawn).  Never required to play -- a missing or corrupt file just means a fresh
profile, so a re-clone or a hand-edit can never lock somebody out.
"""
from __future__ import annotations

import json
import os

from core import config

PATH = os.path.join(config.ROOT, "profile.json")
S_RANK = 420          # must match scenes/results.py rank_of()
DEFAULT_SETTINGS = {"sfx": 0.8, "bgm": 0.25, "path": True}
DEFAULT = {"best": {}, "unlocked": ["easy", "normal"], "runs": 0,
           "settings": dict(DEFAULT_SETTINGS)}


def _clamp(value, fallback):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return fallback
    return 0.0 if value < 0.0 else 1.0 if value > 1.0 else value


def _settings(raw):
    """Merge whatever is on disk over the defaults, clamping junk."""
    out = dict(DEFAULT_SETTINGS)
    if isinstance(raw, dict):
        if "sfx" in raw:
            out["sfx"] = _clamp(raw.get("sfx"), out["sfx"])
        if "bgm" in raw:
            out["bgm"] = _clamp(raw.get("bgm"), out["bgm"])
        if "path" in raw:
            out["path"] = bool(raw.get("path"))
    return out


def _fresh():
    return {"best": {}, "unlocked": list(DEFAULT["unlocked"]), "runs": 0,
            "settings": dict(DEFAULT_SETTINGS)}


def load():
    try:
        with open(PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return _fresh()
    if not isinstance(data, dict):
        return _fresh()
    out = _fresh()
    best = data.get("best")
    if isinstance(best, dict):
        out["best"] = {str(k): int(v) for k, v in best.items()
                       if isinstance(v, (int, float))}
    unlocked = data.get("unlocked")
    if isinstance(unlocked, list):
        out["unlocked"] = [value for value in unlocked if isinstance(value, str)]
    out["runs"] = int(data.get("runs", 0) or 0)
    out["settings"] = _settings(data.get("settings"))
    return out


def save(data):
    try:
        with open(PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except OSError:
        pass          # progress is a nicety; never break a run over it
    return data


def unlocked(data=None):
    return list((data or load())["unlocked"])


def is_unlocked(level, data=None):
    return level in unlocked(data)


def unlock(level, data=None):
    """Open a level outright (redemption code). Returns (data, newly_opened).

    Same file, same ordering rules as record(): the point is that a code and an
    S-grade lead to exactly one unlocked state, not two.
    """
    data = data or load()
    if level in data["unlocked"]:
        return data, None
    data["unlocked"].append(level)
    order = ["easy", "normal", "hard"]
    data["unlocked"] = [name for name in order if name in data["unlocked"]]
    save(data)
    return data, level


def best(level, data=None):
    return int((data or load())["best"].get(level, 0))


def record(level, stars):
    """Store the run. Returns (data, newly_unlocked_level_or_None).

    Challenge mode opens on an S anywhere that is not challenge mode itself:
    the gate is meant to keep a first-timer out, not an S-grade cook.
    """
    data = load()
    data["best"][level] = max(int(data["best"].get(level, 0)), int(stars))
    data["runs"] = int(data.get("runs", 0)) + 1
    opened = None
    if level != "hard" and int(stars) >= S_RANK and "hard" not in data["unlocked"]:
        data["unlocked"].append("hard")
        opened = "hard"
    order = ["easy", "normal", "hard"]
    data["unlocked"] = [name for name in order if name in data["unlocked"]]
    save(data)
    return data, opened


def settings(data=None):
    """The current settings dict (always complete, always clamped)."""
    return dict((data or load()).get("settings") or _settings(None))


def save_settings(patch, data=None):
    """Merge one or more settings keys and persist. Returns the merged dict."""
    data = data or load()
    merged = _settings(data.get("settings"))
    merged.update(_settings(dict(merged, **{k: v for k, v in patch.items()
                                            if k in DEFAULT_SETTINGS})))
    data["settings"] = merged
    save(data)
    return merged
