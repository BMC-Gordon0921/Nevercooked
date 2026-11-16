"""Target acquisition and the single context-sensitive J action."""
from __future__ import annotations

import pygame

from core import config
from game.entities.item import GroundItem
from game.entities.station import Station

def probe_rect(actor, world):
    """Exactly the tile the chef is facing.

    A round/oversized probe bleeds into the corner tiles, which is how you end
    up cooking on the counter you are not looking at.  Snapping to the grid
    means one tile, one target, and no diagonal reach at all.
    """
    room = world.room
    tile = config.TILE
    col = int((actor.foot.centerx - room.x) // tile)
    row = int((actor.foot.centery - room.y) // tile)
    dx, dy = actor.facing
    return pygame.Rect(room.x + (col + dx) * tile, room.y + (row + dy) * tile, tile, tile)


def find_target(world, actor):
    """Nearest interactable covering the tile in front, with 150ms stickiness."""
    probe = probe_rect(actor, world)
    sticky_ms = config.TUNING["interaction"]["sticky_ms"] / 1000.0
    current = actor.target
    if current is not None and getattr(current, "alive", True):
        foot = getattr(current, "reach", None) or current.foot
        if foot.colliderect(probe) and actor.target_age < 0.6:
            return current
    best = None
    best_dist = 1 << 30
    for station in world.stations:
        if not station.reach.colliderect(probe):
            continue
        dist = abs(station.foot.centerx - actor.foot.centerx) + abs(station.foot.centery - actor.foot.centery)
        if dist < best_dist:
            best, best_dist = station, dist
    for entity in world.entities:
        if not isinstance(entity, GroundItem):
            continue
        if not entity.foot.colliderect(probe):
            continue
        dist = abs(entity.foot.centerx - actor.foot.centerx) + abs(entity.foot.centery - actor.foot.centery)
        if dist < best_dist:
            best, best_dist = entity, dist
    if best is not current:
        actor.target_age = 0.0
        if best is not None and sticky_ms > 0:
            pass
    actor.target = best
    return best


def _item_name(item_id):
    return config.ITEMS[item_id]["name"]


def transform_for(stype, item_id):
    for rule in config.TRANSFORMS:
        if rule["station"] == stype and rule["input"] == item_id:
            return rule
    return None


def recipe_for(stype, item_id):
    for rule in config.RECIPES:
        if rule["station"] == stype and rule["base"] == item_id:
            return rule
    return None


def bases_for(stype):
    """The items this station would accept into an empty slot."""
    names = []
    for rule in config.RECIPES:
        if rule["station"] == stype:
            name = _item_name(rule["base"])
            if name not in names:
                names.append(name)
    for rule in config.TRANSFORMS:
        if rule["station"] == stype:
            name = _item_name(rule["input"])
            if name not in names:
                names.append(name)
    return names


def describe(actor, target):
    """What would J do right now? Returns (label, enabled)."""
    if target is None:
        return ("", False)
    hand = actor.hand

    if isinstance(target, GroundItem):
        if hand is None:
            return ("捡起 " + target.item.name, True)
        return ("手上有货", False)

    station = target
    stype = station.stype

    if stype == "crate":
        if hand is not None:
            return ("手上有货", False)
        return ("取 " + _item_name(station.dispense), True)

    if stype == "trash":
        if hand is not None:
            return ("丢掉 " + hand.name, True)
        return ("垃圾桶", False)

    if stype == "serve":
        if hand is not None and hand.is_dish:
            return ("出餐 " + hand.name, True)
        if hand is not None:
            return ("这不是菜", False)
        return ("出餐口", False)

    if stype == "board":
        if station.slot is None:
            if hand is not None and "choppable" in hand.defn["tags"]:
                return ("放上砧板", True)
            return ("空砧板", False)
        if station.phase == Station.PHASE_READY:
            if hand is None:
                return ("拿走 " + station.slot.name, True)
            return ("手上有货", False)
        if hand is None:
            return ("切 " + station.slot.name, True)
        return ("手上有货", False)

    if station.slot is None:
        if hand is None:
            return ("空的" + station.defn["name"], False)
        if transform_for(stype, hand.item_id) or recipe_for(stype, hand.item_id):
            return ("放入 " + hand.name, True)
        names = bases_for(stype)
        if names:
            return ("这里要 " + "/".join(names[:2]), False)
        return ("放不进去", False)

    if station.phase == Station.PHASE_READY:
        if hand is None:
            return ("取出 " + station.slot.name, True)
        return ("手上有货", False)

    if station.phase == Station.PHASE_ADD:
        need = station.pending[0] if station.pending else None
        if need and hand is not None and hand.item_id == need:
            return ("投入 " + hand.name, True)
        return ("还差 " + _item_name(need), False)

    if station.phase == Station.PHASE_COOK:
        return (station.rule.get("verb", "做") + "中…", False)

    return ("空的" + station.defn["name"], False)


def interact(world, actor, target):
    """Run the context action. Returns a short event key for feedback."""
    if target is None:
        return "none"

    if isinstance(target, GroundItem):
        if actor.hand is None:
            world.give_to_hand(actor, target.item)
            target.alive = False
            world.entities.remove(target)
            actor.target = None
            return "pickup"
        return "reject"

    station = target
    stype = station.stype
    hand = actor.hand

    if stype == "crate":
        if hand is not None or station.dispense is None:
            return "reject"
        world.give_to_hand(actor, world.new_item(station.dispense))
        station.flash = 1.0
        return "take"

    if stype == "trash":
        if hand is None:
            return "reject"
        if "dish" in hand.defn["tags"] and hand.quality <= 0.0:
            world.score.burnt_trashed += 1
        world.consume(hand)
        actor.hand = None
        station.flash = 1.0
        return "trash"

    if stype == "serve":
        return world.serve(actor, station)

    if stype == "board":
        if station.slot is None:
            if hand is None or "choppable" not in hand.defn["tags"]:
                return "reject"
            rule = transform_for(stype, hand.item_id)
            if rule is None:
                return "reject"
            world.feed(station, hand)
            actor.hand = None
            station.rule = rule
            station.chops_needed = rule.get("chops", 0)
            station.chops = 0
            station.output = rule["output"]
            station.phase = Station.PHASE_PREP
            station.duration = 0.0
            return "load"
        if station.phase == Station.PHASE_READY:
            if hand is not None:
                return "reject"
            item = station.clear_slot()
            world.give_to_hand(actor, item)
            return "take"
        if hand is not None:
            return "reject"
        # One press finishes the whole chop: no meter, no waiting, no busy lock.
        station.chops = station.chops_needed
        station.flash = 1.0
        world.complete_station(station)
        return "chop_done"

    # heat / assemble stations
    if station.slot is None:
        if hand is None:
            return "reject"
        rule = transform_for(stype, hand.item_id)
        recipe = recipe_for(stype, hand.item_id)
        if rule is None and recipe is None:
            return "reject"
        world.feed(station, hand)
        actor.hand = None
        if rule is not None:
            station.rule = rule
            station.output = rule["output"]
            if rule.get("chops"):
                station.chops_needed = rule["chops"]
                station.phase = Station.PHASE_PREP
            else:
                station.phase = Station.PHASE_COOK
                station.duration = rule.get("duration", 0.0)
                station.timer = 0.0
        else:
            station.rule = recipe
            station.pending = list(recipe["add"])
            station.output = recipe["output"]
            station.phase = Station.PHASE_ADD
        return "load"

    if station.phase == Station.PHASE_READY:
        if hand is not None:
            return "reject"
        item = station.clear_slot()
        world.give_to_hand(actor, item)
        return "take"

    if station.phase == Station.PHASE_ADD:
        need = station.pending[0] if station.pending else None
        if hand is None or need is None or hand.item_id != need:
            return "reject"
        world.consume(hand)
        actor.hand = None
        station.pending.pop(0)
        if not station.pending:
            station.phase = Station.PHASE_COOK
            station.duration = station.rule.get("duration", 0.0)
            station.timer = 0.0
        return "add"

    return "reject"


def throw(world, actor):
    """K: lob whatever is in hand 1.5 tiles forward."""
    if actor.hand is None:
        return "none"
    item = actor.hand
    actor.hand = None
    tiles = config.TUNING["timing"]["throw_tiles"]
    tx, ty = actor.facing
    target = pygame.Rect(0, 0, 16, 16)
    target.center = (actor.foot.centerx + int(tx * config.TILE * tiles),
                     actor.foot.centery + int(ty * config.TILE * tiles))
    world.drop_at(item, target)
    return "throw"
