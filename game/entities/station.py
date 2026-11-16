"""Stations: one footprint, one slot, one small state machine."""
from __future__ import annotations

import pygame

from core import config
from game.entities.base import Entity

_TINTS = {
    "crate": (124, 96, 64),
    "steamer": (150, 160, 176),
    "wok": (86, 92, 104),
    "oven": (128, 92, 70),
    "board": (150, 128, 96),
    "assemble": (110, 126, 150),
    "serve": (66, 108, 132),
    "trash": (86, 90, 96),
}


class Station(Entity):
    PHASE_IDLE = "idle"
    PHASE_PREP = "prep"
    PHASE_ADD = "add"
    PHASE_COOK = "cook"
    PHASE_READY = "ready"

    def __init__(self, stype, foot, label=None, dispense=None, reach=None):
        defn = config.STATION_DEFS[stype]
        super().__init__(foot, "station_" + stype, defn["height"], layer_bias=0,
                         color=_TINTS.get(stype, (120, 128, 140)),
                         label=defn["name"][:1])
        self.stype = stype
        self.defn = defn
        self.label = label or defn["name"]
        self.dispense = dispense
        # Interaction footprint: the whole tile, so standing in front of a machine
        # never grabs the neighbour behind it.
        self.reach = reach.copy() if reach is not None else foot.copy()
        self.slot = None
        self.phase = Station.PHASE_IDLE
        self.timer = 0.0
        self.duration = 0.0
        self.chops = 0
        self.chops_needed = 0
        self.pending = []
        self.rule = None
        self.output = None
        self.burn = 0.0
        self.burn_stage = 0
        self.flash = 0.0

    # -- convenience ----------------------------------------------------
    def clear_slot(self):
        item = self.slot
        self.slot = None
        self.phase = Station.PHASE_IDLE
        self.timer = 0.0
        self.duration = 0.0
        self.chops = 0
        self.chops_needed = 0
        self.pending = []
        self.rule = None
        self.output = None
        self.burn = 0.0
        self.burn_stage = 0
        return item

    def hold(self, item, phase, duration=0.0):
        self.slot = item
        item.owner = self
        item.owner_kind = "station"
        self.phase = phase
        self.timer = 0.0
        self.duration = duration

    @property
    def progress(self):
        if self.duration <= 0:
            return 0.0
        return min(1.0, self.timer / self.duration)

    def update(self, dt):
        self.tick_alpha(dt)
        if self.flash > 0:
            self.flash = max(0.0, self.flash - dt * 4.0)
