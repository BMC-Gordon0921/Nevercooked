"""Items: the only thing that can ever be in a hand, a slot or on the floor."""
from __future__ import annotations

import pygame

from core import config
from game.entities.base import Entity

_counter = [0]


def reset_ids():
    _counter[0] = 0


class Item:
    """A single physical thing. It always has exactly one holder."""

    def __init__(self, item_id):
        _counter[0] += 1
        self.uid = _counter[0]
        self.item_id = item_id
        self.defn = config.ITEMS[item_id]
        self.owner = None
        self.owner_kind = "none"
        self.quality = 1.0
        self.age = 0.0

    @property
    def name(self):
        return self.defn["name"]

    @property
    def icon(self):
        return self.defn["icon"]

    @property
    def is_dish(self):
        return "dish" in self.defn["tags"]

    def __repr__(self):
        return "<Item %s#%d %s>" % (self.item_id, self.uid, self.owner_kind)


class GroundItem(Entity):
    """An item lying on the floor. It never expires and never disappears."""

    def __init__(self, item, foot):
        color = (200, 220, 240) if item.is_dish else (180, 170, 150)
        super().__init__(foot, item.icon, 16, layer_bias=-40, solid=False,
                         color=color, label=None)
        self.item = item
        item.owner = self
        item.owner_kind = "ground"

    def update(self, dt):
        self.tick_alpha(dt)
        self.item.age += dt
