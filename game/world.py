"""World: owns every entity, the room, the item registry and the run clock."""
from __future__ import annotations

import pygame

from core import config
from game.entities.actor import Actor
from game.entities.base import Entity
from game.entities.item import GroundItem, Item, reset_ids
from game.entities.station import Station

WALL_BACK_H = 120
WALL_SIDE_H = 120
WALL_FRONT_H = 44


class World:
    def __init__(self, seed=7):
        reset_ids()
        self.entities = []
        self.stations = []
        self.items = []
        self.popups = []
        self.time = 0.0
        self.paused = False
        self.orders = None
        self.score = None
        self.last_breakdown = None
        layout = config.LAYOUT
        room = layout["room"]
        self.room = pygame.Rect(room["x"], room["y"], room["w"], room["h"])
        # Camera limits: the playable strip.  Exactly one view tall (rows 1..4),
        # so the frame never pans vertically and never shows the heavy front
        # wall; only the horizontal pan follows the cook across the kitchen.
        self.bounds = pygame.Rect(self.room.x, self.room.y + config.TILE // 2,
                                  self.room.w, self.room.h - config.TILE)
        self._build_walls(layout["room"]["wall"])
        self._build_stations(layout["stations"])
        spawn = layout["spawn"]
        self.player = Actor(self._foot_for_tile(*spawn))
        self.entities.append(self.player)
        self.player.foot.midbottom = (self.player.foot.centerx, self.player.foot.bottom)

    # -- construction ---------------------------------------------------
    def tile_rect(self, col, row):
        """Room-relative tile -> screen rect."""
        room = self.room
        return pygame.Rect(room.x + col * config.TILE, room.y + row * config.TILE,
                           config.TILE, config.TILE)

    def _foot_for_tile(self, tx, ty):
        tile = self.tile_rect(tx, ty)
        tuning = config.TUNING["player"]
        foot = pygame.Rect(0, 0, tuning["foot_w"], tuning["foot_h"])
        foot.center = (tile.centerx, tile.centery + 6)
        return foot

    def _build_walls(self, thickness):
        room = self.room
        tiles = config.TILE
        cols = room.w // tiles
        rows = room.h // tiles
        ox, oy = room.x, room.y
        for index in range(cols):
            self._add_wall(ox + index * tiles, oy, "wall_back", WALL_BACK_H)
            self._add_wall(ox + index * tiles, oy + (rows - 1) * tiles, "wall_front", WALL_FRONT_H)
        for index in range(1, rows - 1):
            self._add_wall(ox, oy + index * tiles, "wall_side", WALL_SIDE_H)
            self._add_wall(ox + (cols - 1) * tiles, oy + index * tiles, "wall_side", WALL_SIDE_H)

    def _add_wall(self, x, y, key, height):
        wall = Entity(pygame.Rect(x, y, config.TILE, config.TILE), key, height,
                      layer_bias=-10, solid=True, color=(74, 84, 104), label=None)
        self.entities.append(wall)
        return wall

    def _build_stations(self, entries):
        for entry in entries:
            tx, ty = entry["tile"]
            tile = self.tile_rect(tx, ty)
            foot = pygame.Rect(0, 0, 60, 30)
            foot.midbottom = (tile.centerx, tile.bottom)
            station = Station(entry["type"], foot, entry.get("label"),
                              entry.get("item"), reach=tile)
            self.stations.append(station)
            self.entities.append(station)

    # -- items ----------------------------------------------------------
    def new_item(self, item_id):
        item = Item(item_id)
        self.items.append(item)
        return item

    def give_to_hand(self, actor, item):
        actor.hand = item
        item.owner = actor
        item.owner_kind = "hand"

    def drop_to_floor(self, actor, item):
        drop = GroundItem(item, pygame.Rect(actor.foot.centerx - 8,
                                            actor.foot.bottom - 6, 16, 16))
        self.entities.append(drop)
        actor.hand = None
        return drop

    def feed(self, station, item):
        """Put an item into a station slot (ownership transfers here)."""
        station.slot = item
        item.owner = station
        item.owner_kind = "station"

    def drop_at(self, item, rect):
        """Place an item on the floor at an arbitrary spot (kept inside the room)."""
        foot = pygame.Rect(rect.centerx - 8, rect.centery - 8, 16, 16)
        foot.clamp_ip(self.room.inflate(-config.TILE * 3, -config.TILE * 3))
        drop = GroundItem(item, foot)
        self.entities.append(drop)
        return drop

    def consume(self, item):
        """Remove an item only because it was transformed, served or binned."""
        item.owner = None
        item.owner_kind = "gone"
        if item in self.items:
            self.items.remove(item)

    def complete_station(self, station):
        """A timer or the last chop finished: swap the slot item for the output."""
        old = station.slot
        if old is None or station.output is None:
            return None
        new = self.new_item(station.output)
        new.quality = old.quality
        self.feed(station, new)
        station.phase = Station.PHASE_READY
        station.timer = 0.0
        station.duration = 0.0
        station.burn = 0.0
        station.burn_stage = 0
        self.consume(old)
        self.popup(new.name, (station.foot.centerx, station.foot.top - 8), config.color("spark"))
        return new

    def serve(self, actor, station):
        """Hand a dish over at the pass. Matches the oldest live order."""
        from game.systems import scoring

        item = actor.hand
        if item is None or not item.is_dish:
            return "reject"
        order = self.orders.match(item.item_id) if self.orders else None
        if order is None:
            self.popup("没有这张单", (station.foot.centerx, station.foot.top - 10),
                       config.color("pink"))
            return "no_order"
        breakdown = scoring.settle(order, item.quality, self.score.combo, self.time)
        self.score.add(breakdown)
        self.orders.deliver(order)
        actor.hand = None
        self.consume(item)
        station.flash = 1.0
        self.last_breakdown = breakdown
        self.popup("+%d" % breakdown["income"], (station.foot.centerx, station.foot.top - 10),
                   config.color("lime"))
        return "served"

    # -- feedback -------------------------------------------------------
    def popup(self, text, pos, color=(255, 255, 255), life=1.1):
        self.popups.append({"text": text, "x": pos[0], "y": pos[1], "color": color,
                            "life": life, "max": life})

    # -- frame ----------------------------------------------------------
    def update(self, dt):
        self.time += dt
        for entity in self.entities:
            entity.update(dt)
        for popup in self.popups:
            popup["life"] -= dt
            popup["y"] -= 26 * dt
        self.popups = [p for p in self.popups if p["life"] > 0]

    def solids(self):
        return [e for e in self.entities if e.solid]

    def validate(self):
        """Every live item must be held by exactly one holder."""
        holders = {}
        for station in self.stations:
            if station.slot is not None:
                holders[id(station.slot)] = holders.get(id(station.slot), 0) + 1
        if self.player.hand is not None:
            holders[id(self.player.hand)] = holders.get(id(self.player.hand), 0) + 1
        for entity in self.entities:
            if isinstance(entity, GroundItem):
                holders[id(entity.item)] = holders.get(id(entity.item), 0) + 1
        problems = []
        for item in self.items:
            count = holders.get(id(item), 0)
            if count != 1:
                problems.append("%r held by %d" % (item, count))
        return problems
