"""Order of operations, derived from data/dishes.json.

The point is that nothing here hard-codes a dish: a new recipe in the JSON gets
a guide chain for free.  Used for the "next step" line and the pulse mark on
whichever machine is next.
"""
from __future__ import annotations

from core import config

RAW_CACHE = {}


def _producers():
    """output item -> ("transform"|"recipe", row)"""
    table = {}
    for row in config.TRANSFORMS:
        table[row["output"]] = ("transform", row)
    for row in config.RECIPES:
        table[row["output"]] = ("recipe", row)
    return table


def chain(item_id, depth=0):
    """Ordered steps to build an item from raw crates."""
    if depth > 8:
        return []
    table = _producers()
    entry = table.get(item_id)
    if entry is None:
        return []
    kind, row = entry
    if kind == "transform":
        return chain(row["input"], depth + 1) + [{
            "station": row["station"],
            "verb": row.get("verb", "做"),
            "item": row["input"],
            "out": row["output"],
        }]
    steps = []
    steps += chain(row["base"], depth + 1)
    for extra in row.get("add", []):
        steps += chain(extra, depth + 1)
    steps.append({
        "station": row["station"],
        "verb": row.get("verb", "做"),
        "item": row["base"],
        "out": row["output"],
        "add": list(row.get("add", [])),
    })
    return steps


def steps(dish_id):
    if dish_id not in RAW_CACHE:
        RAW_CACHE[dish_id] = chain(dish_id)
    return RAW_CACHE[dish_id]


def needed_items(dish_id):
    out = set()
    for step in steps(dish_id):
        out.add(step["item"])
        out.add(step["out"])
        out.update(step.get("add", []))
    return out


def _station(world, stype, prefer_idle=True):
    pool = [s for s in world.stations if s.stype == stype]
    if not pool:
        return None
    if prefer_idle:
        for station in pool:
            if station.phase == "idle":
                return station
    for station in pool:
        if station.phase in ("idle", "ready"):
            return station
    return pool[0]


def _serve_station(world):
    return next((s for s in world.stations if s.stype == "serve"), None)


def current_order(world):
    """The oldest ticket still waiting: that is the one to cook for."""
    if world.orders is None:
        return None
    active = [o for o in world.orders.active if o.state == "active"]
    if not active:
        return None
    return max(active, key=lambda o: o.age)


def next_step(world, actor):
    """Returns {"label": str, "station": Station|None} or None."""
    order = current_order(world)
    if order is None or not steps(order.dish_id):
        return None
    plan = steps(order.dish_id)
    dish_name = config.DISHES[order.dish_id]["name"]
    hand = actor.hand

    # 1. holding today's dish: the only remaining step is the pass
    if hand is not None and hand.item_id == order.dish_id:
        return {"label": "去出餐口 交 %s" % dish_name, "station": _serve_station(world)}

    # 2. something finished and waiting on a machine we still need
    wanted = needed_items(order.dish_id)
    for station in world.stations:
        if station.phase == "ready" and station.slot is not None:
            if station.slot.item_id in wanted:
                return {"label": "去%s 取 %s" % (station.label, station.slot.name),
                        "station": station}

    # 3. carry it to the machine that consumes it
    if hand is not None:
        for step in plan:
            if step["item"] == hand.item_id:
                station = _station(world, step["station"])
                if station is not None:
                    return {"label": "去%s %s %s" % (station.label, step["verb"],
                                                     hand.name),
                            "station": station}
            if hand.item_id in step.get("add", []):
                station = _station(world, step["station"])
                if station is not None:
                    return {"label": "去%s 放 %s" % (station.label, hand.name),
                            "station": station}
        return {"label": "%s 这张单用不上，扔进垃圾桶" % hand.name,
                "station": next((s for s in world.stations
                                 if s.stype == "trash"), None)}

    # 4. something is already on the fire: wait for it
    for station in world.stations:
        if station.phase in ("cook", "add"):
            return {"label": "等%s（%s）" % (station.label,
                                            station.slot.name if station.slot else "…"),
                    "station": station}

    # 5. empty hands: fetch the first raw input of the chain
    first = plan[0]
    crate = None
    for station in world.stations:
        if station.stype == "crate" and station.dispense == first["item"]:
            crate = station
            break
    if crate is not None:
        return {"label": "去%s 拿 %s" % (crate.label,
                                        config.ITEMS[first["item"]]["name"]),
                "station": crate}
    return {"label": "先把 %s 备好" % dish_name, "station": None}
