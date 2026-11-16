"""Station timers, transformations, burn progression and serving."""
from __future__ import annotations

from core import config
from game.entities.station import Station

BURN_STAGE1 = 6.0
BURN_STAGE2 = 12.0


def tick_station(world, station, dt):
    if station.phase == Station.PHASE_COOK:
        station.timer += dt
        if station.duration > 0 and station.timer >= station.duration:
            world.complete_station(station)
        return
    if station.phase == Station.PHASE_READY and station.defn.get("heat"):
        station.burn += dt
        if station.burn >= BURN_STAGE2:
            stage = 2
        elif station.burn >= BURN_STAGE1:
            stage = 1
        else:
            stage = 0
        if stage != station.burn_stage:
            station.burn_stage = stage
            if station.slot is not None:
                station.slot.quality = (1.0, 0.7, 0.0)[stage]
            word = ("", "过火", "糊了")[stage]
            if word:
                world.popup(word, (station.foot.centerx, station.foot.top - 6),
                           (255, 154, 60) if stage == 1 else (224, 69, 47))


def tick_all(world, dt):
    for station in world.stations:
        tick_station(world, station, dt)
