"""Money maths, kept in one place so the rules stay auditable."""
from __future__ import annotations

import math

from core import config

CFG = config.TUNING["scoring"]


def freshness(order):
    """1.0 on time, 0.7 within 20% overdue, 0.4 within 50%, else 0."""
    overdue = order.overdue
    if overdue <= 0.0:
        return CFG["fresh_full"]
    if overdue <= order.patience * CFG["late_small_ratio"]:
        return CFG["fresh_late_small"]
    if overdue <= order.patience * CFG["late_big_ratio"]:
        return CFG["fresh_late_big"]
    return 0.0


def combo_multiplier(combo):
    return min(1.0 + CFG["combo_step"] * combo, CFG["combo_cap"])


def settle(order, quality, combo, elapsed):
    """Return a dict with the full breakdown of one delivery."""
    rush = CFG["rush_multiplier"] if elapsed >= CFG["rush_from"] else 1.0
    fresh = min(freshness(order), quality)
    mult = combo_multiplier(combo)
    base = order.price * rush
    tip = order.price * CFG["tip_ratio"] * order.patience_ratio
    income = base * fresh * mult + tip
    return {
        "base": round(base, 1),
        "fresh": fresh,
        "mult": mult,
        "tip": round(tip, 1),
        "income": int(round(income)),
        "rush": rush,
    }


class ScoreBoard:
    def __init__(self):
        self.stars = 0
        self.combo = 0
        self.best_combo = 0
        self.income = 0
        self.tips = 0
        self.served = 0
        self.failed = 0
        self.burnt_trashed = 0
        self.last = None

    def add(self, breakdown):
        self.income += breakdown["income"]
        self.tips += int(round(breakdown["tip"]))
        self.served += 1
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self.last = breakdown

    def break_combo(self):
        self.combo = 0

    def on_fail(self):
        self.failed += 1
        self.combo = 0

    def final_stars(self):
        penalty = CFG["penalty_burnt"] * self.burnt_trashed + CFG["penalty_unserved"] * self.failed
        return int(self.income - penalty)

    def coins(self):
        return int(math.floor(max(0, self.final_stars()) * CFG["coin_ratio"]))
