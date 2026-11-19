"""Target acquisition and the single context-sensitive F action.

Everything the prompt promises and everything F does comes from one place now:
`_plan()`.  The old code had `describe()` and `interact()` walking separate
if-chains, so the HUD could say "hand full" and F could still run a different
branch; together with a floor clamp that collapsed the room into one line, that
is what made the stations feel jammed.
"""
from __future__ import annotations

import pygame

from core import config
from game.entities.item import GroundItem
from game.entities.station import Station
from game.systems import difficulty
from game.systems.tasking import PLAYER


# ---------------------------------------------------------------- geometry
def cell_of(actor, world):
    tile = config.TILE
    return (int((actor.foot.centerx - world.room.x) // tile),
            int((actor.foot.centery - world.room.y) // tile))


def tile_rect(world, col, row):
    return pygame.Rect(world.room.x + col * config.TILE,
                       world.room.y + row * config.TILE, config.TILE, config.TILE)


def facing_rect(actor, world):
    """The tile the chef is looking at (the original, exact rule)."""
    col, row = cell_of(actor, world)
    dx, dy = actor.facing
    return tile_rect(world, col + dx, row + dy)


def foot_tiles(actor, world):
    """Every tile the foot box really touches - a 24x16 foot straddles seams."""
    tile = config.TILE
    room = world.room
    left = max(room.x, actor.foot.left - 2)
    right = min(room.right - 1, actor.foot.right + 2)
    top = max(room.y, actor.foot.top - 2)
    bottom = min(room.bottom - 1, actor.foot.bottom + 2)
    cols = sorted({int((left - room.x) // tile), int((right - room.x) // tile)})
    rows = sorted({int((top - room.y) // tile), int((bottom - room.y) // tile)})
    return [(c, r) for r in rows for c in cols]


def ring_tiles(actor, world, radius=1):
    """(col, row, dc, dr) for the cook's tile and its neighbours."""
    cols = world.room.w // config.TILE
    rows = world.room.h // config.TILE
    col, row = cell_of(actor, world)
    out = []
    for dr in range(-radius, radius + 1):
        for dc in range(-radius, radius + 1):
            c, r = col + dc, row + dr
            if 0 <= c < cols and 0 <= r < rows:
                out.append((c, r, dc, dr))
    return out


def _dist(entity, actor):
    return (abs(entity.foot.centerx - actor.foot.centerx)
            + abs(entity.foot.centery - actor.foot.centery))


def _station_in_tile(world, rect, actor):
    """The station whose own tile holds this rect - nearest to the cook wins.

    Matched by the tile's centre, not by rect overlap: two counters sharing a
    seam overlap by a pixel or two after any tolerance, and that is exactly how
    standing between them used to grab the wrong one.
    """
    best = None
    best_score = 1 << 30
    for station in world.stations:
        if not station.reach.collidepoint(rect.centerx, rect.centery):
            continue
        score = _dist(station, actor)
        if score < best_score:
            best, best_score = station, score
    return best


def _loose_in_tile(world, rect, actor):
    best = None
    best_score = 1 << 30
    for entity in world.entities:
        if not isinstance(entity, GroundItem) or not entity.alive:
            continue
        if not entity.foot.colliderect(rect):
            continue
        score = _dist(entity, actor)
        if score < best_score:
            best, best_score = entity, score
    return best


#: Plans that consume what the cook is holding.
HAND_KINDS = ("load", "add", "swap", "serve", "trash")


def takes_hand(actor, station, world):
    """Would this station do something with what the cook holds right now?"""
    if actor.hand is None or world is None:
        return False
    return _plan(actor, station, world)["kind"] in HAND_KINDS


def nearby_taker(actor, world, radius=1):
    """Nearest station around the cook that would take what he is holding."""
    if actor.hand is None or world is None:
        return None
    best = None
    best_key = None
    for (col, row, dc, dr) in ring_tiles(actor, world, radius):
        station = _station_in_tile(world, tile_rect(world, col, row), actor)
        if station is None or not takes_hand(actor, station, world):
            continue
        key = (abs(dc) + abs(dr), _dist(station, actor))
        if best_key is None or key < best_key:
            best, best_key = station, key
    return best


def _in_tile(world, rect, actor, stations=True):
    """Station or ground item belonging to this tile.

    A loose item normally wins the tile, but not when the hands are full and the
    machine right here would take what the cook is carrying: then the machine is
    what he came for and the egg on the floor waits for the next press.
    """
    station = _station_in_tile(world, rect, actor) if stations else None
    loose = _loose_in_tile(world, rect, actor)
    if station is None or loose is None:
        return station if loose is None else loose
    return station if takes_hand(actor, station, world) else loose


def _rank(world, actor, entity, dc, dr, foot=False):
    """Sort key for loose aim; lower is better.

    With a full hand a machine that would take it outranks everything else, and
    tiles under the feet come before the ring.  That is the difference between
    "the rice goes in the wok" and "the cook grabs the egg and drops the rice".
    """
    if isinstance(entity, GroundItem):
        tier = 1 if actor.hand is not None else 0
    else:
        tier = 0 if takes_hand(actor, entity, world) else (2 if actor.hand is not None else 1)
    dx, dy = actor.facing
    dot = dc * dx + dr * dy
    return (tier, 0 if foot else 1, -dot, abs(dc) + abs(dr), _dist(entity, actor))


def _reachable(entity, actor, world):
    if isinstance(entity, GroundItem):
        return _dist(entity, actor) <= config.TILE * 2
    col, row = cell_of(actor, world)
    for (c, r, dc, dr) in ring_tiles(actor, world, 1):
        if entity.reach.colliderect(tile_rect(world, c, r)):
            return True
    return False


def resolve(actor, world):
    """Pick the one thing F would act on.

    Order: exactly what the chef looks at, then the tiles under the feet, then
    one ring around the cook ordered by how much it is in front of them.
    """
    facing = facing_rect(actor, world)
    best = _in_tile(world, facing, actor)
    if best is not None:
        return _settle(actor, world, best)
    if not difficulty.assist("loose_aim"):
        return _settle(actor, world, None)

    candidates = []
    for (col, row) in foot_tiles(actor, world):
        # Only loose items here: a solid machine cannot share a tile with the
        # cook, so anything found underfoot is a dropped dish or a crate lid.
        found = _loose_in_tile(world, tile_rect(world, col, row), actor)
        if found is not None:
            candidates.append((_rank(world, actor, found, 0, 0, foot=True), found))
    for (col, row, dc, dr) in ring_tiles(actor, world, 1):
        if dc == 0 and dr == 0:
            continue
        rect = tile_rect(world, col, row)
        for found in (_station_in_tile(world, rect, actor),
                      _loose_in_tile(world, rect, actor)):
            if found is not None:
                candidates.append((_rank(world, actor, found, dc, dr), found))
    if not candidates:
        return _settle(actor, world, None)
    candidates.sort(key=lambda c: c[0])
    return _settle(actor, world, candidates[0][1])


def _settle(actor, world, candidate):
    """Keep the current target only while nothing else is picked (no lag)."""
    sticky = config.TUNING["interaction"]["sticky_ms"] / 1000.0
    current = actor.target
    if (candidate is None and current is not None
            and getattr(current, "alive", True)
            and actor.target_age < sticky and _reachable(current, actor, world)):
        return current
    if candidate is not current:
        actor.target_age = 0.0
    actor.target = candidate
    return candidate


def find_target(world, actor):
    """Back-compat alias: the old name for resolve()."""
    return resolve(actor, world)


# ------------------------------------------------------------------- rules
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


def _start_station(world, station, item):
    """Feed a slot from the hand. Returns True when the station took it."""
    stype = station.stype
    rule = transform_for(stype, item.item_id)
    recipe = recipe_for(stype, item.item_id)
    if stype == "board":
        if rule is None or "choppable" not in item.defn["tags"]:
            return False
        world.feed(station, item)
        station.rule = rule
        station.chops_needed = rule.get("chops", 0)
        station.chops = 0
        station.output = rule["output"]
        station.phase = Station.PHASE_PREP
        station.duration = 0.0
        return True
    if rule is None and recipe is None:
        return False
    world.feed(station, item)
    if rule is not None:
        station.rule = rule
        station.output = rule["output"]
        if rule.get("chops"):
            station.chops_needed = rule["chops"]
            station.chops = 0
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
    return True


def _plan(actor, target, world):
    """The single source of truth for both the prompt and the F key."""
    hand = actor.hand
    auto_free = difficulty.assist("auto_free_hand")

    def plan(kind, label, ok, detail="", **extra):
        extra.update({"kind": kind, "label": label, "ok": ok, "detail": detail})
        return extra

    if target is None:
        if hand is not None:
            # F never drops an item the machine next to you was waiting for.
            # Hard mode aims strictly, so a step off the tile used to turn
            # "put the rice in the wok" into "throw the rice on the floor".
            taker = nearby_taker(actor, world)
            if taker is not None:
                return plan("noop", "面朝 " + taker.defn["name"] + " 再按 F", False,
                            "这台要 " + hand.name + "，别丢地上")
            return plan("drop", "放下 " + hand.name, True, "F 放下 · Q 抛出")
        return plan("noop", "", False, "")

    if isinstance(target, GroundItem):
        if hand is None:
            return plan("pickup", "捡起 " + target.item.name, True)
        if auto_free:
            return plan("swap_pickup", "换手捡起 " + target.item.name, True,
                        "手上的 " + hand.name + " 会放到脚边")
        return plan("noop", "手上有货", False, "先按 F 放下，或 Q 抛出")

    station = target
    stype = station.stype
    empty = station.slot is None

    # The helper is mid-operation on this machine: the player still has the last
    # word, but not through the middle of somebody else's batch.  A second tap
    # (after the board hands the station to the player) does get through.
    board = getattr(world, "tasks", None)
    if board is not None and stype not in ("crate", "trash", "serve"):
        held = board.station_owner(station)
        other = getattr(getattr(held, "brain", None), "actor", None)
        # A lease held by *another* cook's mission, mid-batch, is a reject with a
        # reason.  Your own mission never blocks you, and a finished batch is
        # always yours to take.
        if (other is not None and other is not actor
                and station.phase in ("prep", "add", "cook")):
            name = station.defn.get("name", "设备")
            who = "帮厨" if getattr(other, "role", "") == "helper" else "另一位厨师"
            return plan("noop", who + "正在用" + name, False,
                        "%s正在用这台%s，等他做完" % (who, name))

    if stype == "crate":
        if hand is None:
            return plan("take", "取 " + _item_name(station.dispense), True)
        if auto_free:
            return plan("take_free", "取 " + _item_name(station.dispense), True,
                        "手上的 " + hand.name + " 会放到脚边")
        return plan("noop", "手上有货", False, "先按 F 放下，或 Q 抛出")

    if stype == "trash":
        if hand is not None:
            return plan("trash", "丢掉 " + hand.name, True)
        return plan("noop", "垃圾桶", False, "手上有东西才能丢")

    if stype == "serve":
        if hand is not None and hand.is_dish:
            return plan("serve", "出餐 " + hand.name, True)
        if hand is not None:
            return plan("noop", "出餐口只收成菜", False, "你拿着 " + hand.name)
        return plan("noop", "出餐口", False, "端一盘成菜过来")

    # -- take from a finished station -----------------------------------
    def take_plan(verb):
        if hand is None:
            return plan("take_slot", verb + " " + station.slot.name, True)
        if _start_station_can_accept(station, hand):
            if difficulty.assist("swap"):
                return plan("swap", "换手：" + verb + " " + station.slot.name, True,
                            "同时放入 " + hand.name)
        if auto_free:
            return plan("take_free_slot", verb + " " + station.slot.name, True,
                        "手上的 " + hand.name + " 会放到脚边")
        return plan("noop", "手上有货", False, "先按 F 放下，或 Q 抛出")

    if stype == "board":
        if empty:
            if hand is None:
                return plan("noop", "空砧板", False, "拿 陨石肉 或 氧气菜 过来")
            if transform_for(stype, hand.item_id) and "choppable" in hand.defn["tags"]:
                return plan("load", "放上砧板", True)
            return plan("noop", "这台切肉和菜", False, "你拿着 " + hand.name)
        if station.phase == Station.PHASE_READY:
            return take_plan("拿走")
        if hand is None:
            return plan("chop", "切 " + station.slot.name, True, "一刀切完")
        if auto_free:
            return plan("chop_free", "切 " + station.slot.name, True,
                        "手上的 " + hand.name + " 会放到脚边")
        return plan("noop", "手上有货", False, "先按 F 放下，或 Q 抛出")

    if empty:
        if hand is None:
            names = bases_for(stype)
            hint = ("这里要 " + "/".join(names[:2])) if names else "空的" + station.defn["name"]
            return plan("noop", station.defn["name"], False, hint)
        if transform_for(stype, hand.item_id) or recipe_for(stype, hand.item_id):
            return plan("load", "放入 " + hand.name, True)
        names = bases_for(stype)
        if names:
            return plan("noop", "这台要 " + "/".join(names[:2]), False, "你拿着 " + hand.name)
        return plan("noop", "放不进去", False, "这台不吃 " + hand.name)

    if station.phase == Station.PHASE_READY:
        return take_plan("取出")

    if station.phase == Station.PHASE_ADD:
        need = station.pending[0] if station.pending else None
        if need and hand is not None and hand.item_id == need:
            return plan("add", "投入 " + hand.name, True)
        hint = ("还差 " + _item_name(need)) if need else "还差料"
        if hand is not None:
            hint += "，你拿着 " + hand.name
        return plan("noop", hint, False, "按顺序投料")

    if station.phase == Station.PHASE_COOK:
        return plan("noop", station.defn["name"] + " " + _percent(station), False,
                    "等它好，或先去做别的")
    return plan("noop", "空的" + station.defn["name"], False, "")


def _start_station_can_accept(station, item):
    stype = station.stype
    if stype == "board":
        return bool(transform_for(stype, item.item_id)) and "choppable" in item.defn["tags"]
    return bool(transform_for(stype, item.item_id) or recipe_for(stype, item.item_id))


def _percent(station):
    if station.duration <= 0:
        return ""
    return "%d%%" % int(round(station.progress * 100))


def describe(actor, target, world=None):
    """What would F do right now? Returns (label, enabled)."""
    plan = _plan(actor, target, world)
    return (plan["label"], plan["ok"])


def explain(actor, target, world=None):
    """(label, detail) for the head label's second line."""
    plan = _plan(actor, target, world)
    return (plan["label"], plan["detail"])


def suggestions(world, actor):
    """Stations that would accept what is in hand (the '!' badges)."""
    if actor.hand is None:
        return []
    out = []
    for station in world.stations:
        plan = _plan(actor, station, world)
        if plan["ok"] and plan["kind"] in ("load", "add", "swap"):
            out.append(station)
    return out


# ------------------------------------------------------------------ verbs
def _take_slot(world, actor, station):
    item = station.clear_slot()
    world.give_to_hand(actor, item)
    return "take"


def interact_with_detail(world, actor, target):
    """Run the plan. Returns (event, detail)."""
    plan = _plan(actor, target, world)
    kind = plan["kind"]
    detail = plan.get("detail", "")
    hand = actor.hand

    if kind == "noop":
        return ("reject", detail or plan["label"])
    if kind == "drop":
        world.drop_to_floor(actor, hand)
        return ("drop", "放下了")
    if kind == "pickup":
        world.give_to_hand(actor, target.item)
        target.alive = False
        if target in world.entities:
            world.entities.remove(target)
        actor.target = None
        return ("pickup", "")
    if kind == "swap_pickup":
        old = hand
        world.give_to_hand(actor, target.item)
        target.alive = False
        if target in world.entities:
            world.entities.remove(target)
        world.drop_at(old, pygame.Rect(actor.foot.centerx, actor.foot.bottom, 1, 1), actor)
        actor.target = None
        return ("pickup", "换手了")
    if kind == "take":
        item = world.new_item(target.dispense)
        world.give_to_hand(actor, item)
        target.flash = 1.0
        return ("take", "")
    if kind == "take_free":
        world.drop_to_floor(actor, hand)
        item = world.new_item(target.dispense)
        world.give_to_hand(actor, item)
        target.flash = 1.0
        return ("take", "手上的放到脚边了")
    if kind == "trash":
        if "dish" in hand.defn["tags"] and hand.quality <= 0.0:
            world.score.burnt_trashed += 1
        world.consume(hand)
        actor.hand = None
        target.flash = 1.0
        return ("trash", "")
    if kind == "serve":
        event = world.serve(actor, target)
        return (event, "")
    if kind == "load":
        if not _start_station(world, target, hand):
            return ("reject", "放不进去")
        actor.hand = None
        return ("load", "")
    if kind == "chop":
        target.chops = target.chops_needed
        target.flash = 1.0
        world.complete_station(target)
        return ("chop_done", "")
    if kind == "chop_free":
        world.drop_to_floor(actor, hand)
        target.chops = target.chops_needed
        target.flash = 1.0
        world.complete_station(target)
        return ("chop_done", "手上的放到脚边了")
    if kind == "take_slot":
        _take_slot(world, actor, target)
        return ("take", "")
    if kind == "take_free_slot":
        world.drop_to_floor(actor, hand)
        _take_slot(world, actor, target)
        return ("take", "手上的放到脚边了")
    if kind == "swap":
        held = hand
        item = target.clear_slot()
        if not _start_station(world, target, held):
            # put the finished item back and refuse: the plan promised a swap
            world.feed(target, item)
            target.phase = Station.PHASE_READY
            return ("reject", "换不进去")
        actor.hand = None
        world.give_to_hand(actor, item)
        return ("swap", "")
    if kind == "add":
        world.consume(hand)
        actor.hand = None
        target.pending.pop(0)
        if not target.pending:
            target.phase = Station.PHASE_COOK
            target.duration = target.rule.get("duration", 0.0)
            target.timer = 0.0
        return ("add", "")
    return ("reject", "")


def interact(world, actor, target):
    """Run the context action. Returns a short event key for feedback."""
    event, _detail = interact_with_detail(world, actor, target)
    return event


def drop(world, actor):
    if actor.hand is None:
        return "none"
    world.drop_to_floor(actor, actor.hand)
    return "drop"


def throw(world, actor):
    """Q: lob whatever is in hand 1.5 tiles forward (see throwing.py)."""
    from game.systems import throwing
    return throwing.throw(world, actor)
