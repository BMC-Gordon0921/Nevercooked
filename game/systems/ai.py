"""Chef brain: a mission planner that runs the kitchen like a pipeline.

Why a planner and not a script.  Three dishes share one wok, one steamer, one
oven, one board, one bench and one pair of hands.  A scripted chain cooks one
ticket at a time and spends most of the round watching a timer; the planner
keeps two tickets in flight, parks the one that is only waiting on a timer and
fills the gap with work from the other, so the wok, the steamer and the oven
are busy in parallel while the single hand slot is never stranded.

Vocabulary
  recipe graph  built from data/dishes.json, so a new dish needs no new code.
  phase         one hand-sized unit of work: pick one thing up, put it down.
                Every phase starts with an empty hand and ends with an empty
                hand - the only shape a one-hand cook can never deadlock on.
  mission       the phases that build one dish for one live ticket.  The phases
                form a small dependency graph instead of a straight line, so the
                oven can bake while the board is being used.
  Brain.think   one Intent per frame: pick a legal phase, walk to the station
                with nav's A*, face it, press F.

Everything tunable lives in data/ai.json; see DEFAULT_PROFILES for the keys.
"""
from __future__ import annotations

import json
import os
import random

from core import config
from core.input import Intent
from game.systems import interaction, nav

DONE, TODO, BLOCKED = "done", "todo", "blocked"

IDLE, PREP, ADD, COOK, READY = ("idle", "prep", "add", "cook", "ready")

#: The stations that can only be used by one dish at a time.  Crates are
#: infinite and the pass is stateless, so neither is ever reserved.
MACHINES = ("steamer", "wok", "oven", "board", "assemble")

DEFAULT_PROFILES = {
    "strong": {
        "dwell": 0.0,        # forced pause after every action, seconds
        "lookahead": 2,      # how many tickets may be in flight at once
        "flex": 0,           # spare ticket slots kept open for parallel work
        "skip": 0.0,         # chance of taking a worse-but-legal job
        "max_orders": 3,     # how many tickets feed the mission planner
        "idle_wait": 0.0,    # standing still after a dish is finished
        "sprint": True,
        "burn_urgent": 1.5,  # seconds on a hot plate that force a rescue grab
        "hand_timeout": 20.0,
        "turn_slack": 12.0,  # px inside a tile still considered aligned
        "stuck": 22.0,       # seconds without progress before a mission is dropped
        "cooldown": 10.0,    # seconds that dish is not retried after being dropped
    },
    "relaxed": {
        "dwell": 1.15,
        "lookahead": 1,
        "skip": 0.22,
        "max_orders": 1,
        "idle_wait": 6.0,
        "sprint": False,
        "burn_urgent": 1.5,
        "hand_timeout": 20.0,
        "turn_slack": 12.0,
        "stuck": 40.0,
        "cooldown": 14.0,
    },
}

FALLBACK = DEFAULT_PROFILES["strong"]


# --------------------------------------------------------------- tuning data
def load_profiles():
    """data/ai.json merged over the built-in defaults."""
    path = os.path.join(config.DATA_DIR, "ai.json")
    raw = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError):
        raw = {}
    table = {}
    for name, base in DEFAULT_PROFILES.items():
        params = dict(base)
        extra = raw.get(name) if isinstance(raw, dict) else None
        if isinstance(extra, dict):
            params.update(extra)
        table[name] = params
    if isinstance(raw, dict):
        for name, extra in raw.items():
            if name not in table and isinstance(extra, dict):
                params = dict(FALLBACK)
                params.update(extra)
                table[name] = params
    return table


# ------------------------------------------------------------ recipe graph
def _producer_table():
    table = {}
    for row in config.TRANSFORMS:
        table[row["output"]] = {
            "kind": "transform", "station": row["station"],
            "input": row["input"], "output": row["output"],
            "chops": int(row.get("chops", 0) or 0),
        }
    for row in config.RECIPES:
        table[row["output"]] = {
            "kind": "recipe", "station": row["station"],
            "base": row["base"], "add": list(row.get("add") or ()),
            "output": row["output"],
        }
    return table


PRODUCERS = _producer_table()


class _Spec:
    """A phase before it is bound to real station objects."""

    __slots__ = ("steps", "deps")

    def __init__(self, steps, deps=()):
        self.steps = list(steps)
        self.deps = tuple(deps)


def _build_spec(item, depth=0):
    """(phases, emit) for one item; phases leave it ready in its station.

    emit is the step that lifts it into a hand: a crate fetch for a raw item,
    a take from the machine that made it otherwise.
    """
    if depth > 8:
        return None, None
    prod = PRODUCERS.get(item)
    if prod is None:
        return [], ("fetch", None, item)
    station = prod["station"]
    if prod["kind"] == "transform":
        sub, emit = _build_spec(prod["input"], depth + 1)
        if sub is None:
            return None, None
        phase = _Spec([emit, ("load", station, prod["input"])], sub)
        if prod["chops"]:
            phase.steps.append(("chop", station, None))
        return sub + [phase], ("take", station, prod["output"])
    sub, emit = _build_spec(prod["base"], depth + 1)
    if sub is None:
        return None, None
    load = _Spec([emit, ("load", station, prod["base"])], sub)
    phases = sub + [load]
    last = load
    for extra in prod["add"]:
        more, emit_extra = _build_spec(extra, depth + 1)
        if more is None:
            return None, None
        add = _Spec([emit_extra, ("add", station, extra)], list(more) + [last])
        phases += more + [add]
        last = add
    return phases, ("take", station, prod["output"])


_SPECS = {}


def dish_spec(dish_id):
    """Cached phase graph for one dish, ending with the pass."""
    if dish_id not in _SPECS:
        phases, emit = _build_spec(dish_id)
        if phases is None:
            _SPECS[dish_id] = None
        else:
            # The pass comes last and must wait for the dish to exist: without
            # that edge the serve phase is legal from frame one, completes on an
            # empty hand and the mission "finishes" before it cooked anything.
            phases = phases + [_Spec([emit, ("serve", "serve", dish_id)], [phases[-1]])]
            _SPECS[dish_id] = phases
    return _SPECS[dish_id]


# ------------------------------------------------------------------ pieces
class Step:
    """One press of F, plus everything needed to judge whether it is legal."""

    __slots__ = ("kind", "station", "item", "nxt")

    def __init__(self, kind, station, item=None):
        self.kind = kind
        self.station = station
        self.item = item
        self.nxt = None         # the step this one hands its item to

    def __repr__(self):
        return "<%s %s %s>" % (self.kind, getattr(self.station, "stype", "?"), self.item)


class Phase:
    """A hand-sized run of steps: acquire one thing, deliver it."""

    __slots__ = ("steps", "deps", "i", "done", "machines")

    def __init__(self, steps, deps=()):
        self.steps = list(steps)
        self.deps = list(deps)
        self.i = 0
        self.done = not self.steps
        seen = []
        for step in self.steps:
            station = step.station
            if station.stype in MACHINES and station not in seen:
                seen.append(station)
        self.machines = seen

    def current(self):
        return None if self.done else self.steps[self.i]


class Mission:
    """Everything one dish needs, for one live ticket."""

    __slots__ = ("dish", "phases", "tag", "age", "last_progress")

    def __init__(self, dish, phases, tag=None):
        self.dish = dish
        self.phases = phases
        self.tag = tag
        self.age = 0.0
        self.last_progress = 0.0

    @property
    def finished(self):
        return all(phase.done for phase in self.phases)


def can_feed(station, item_id):
    """Would this machine take this item as its base (same rule as F)?"""
    stype = station.stype
    if stype == "board":
        return (interaction.transform_for(stype, item_id) is not None
                and "choppable" in config.ITEMS[item_id]["tags"])
    return (interaction.transform_for(stype, item_id) is not None
            or interaction.recipe_for(stype, item_id) is not None)


# ------------------------------------------------------------------- brain
class Brain:
    """Plans the kitchen, then drives the cook one frame at a time."""

    def __init__(self, profile="strong"):
        table = load_profiles()
        self.profile = profile if profile in table else "strong"
        self.params = dict(table[self.profile])
        self.reset()

    # -- lifecycle ------------------------------------------------------
    def reset(self):
        self.missions = []
        self.reserved = {}
        self.cool = {}
        self.rng = random.Random(7)
        self.pre = None         # a pre-steamed rice, waiting for a ticket
        self.t = 0.0
        self.pause = 0.0
        self.idle_left = 0.0
        self.hand_time = 0.0
        self.job = ""           # last chosen step, for the demo overlay
        self._elapsed = None
        self._goal = None       # (id(station), cell) we are walking to
        self._path = None
        self._path_key = None
        self._index_cache = None
        self._index_world = None

    # -- frame ----------------------------------------------------------
    def think(self, scene):
        intent = Intent()
        world = scene.world
        dt = self._dt(scene)
        self.t += dt
        self._sweep(scene, dt)
        if self.pause > 0.0:
            self.pause = max(0.0, self.pause - dt)
            return intent
        if self.idle_left > 0.0:
            self.idle_left = max(0.0, self.idle_left - dt)
            return intent
        pick = self._choose(world)
        if pick is None:
            self._drift(scene, intent)
            return intent
        self._act(scene, pick, intent)
        return intent

    def _dt(self, scene):
        elapsed = getattr(scene, "elapsed", None)
        if elapsed is None:
            return 1.0 / 60.0
        if self._elapsed is None:
            self._elapsed = elapsed
            return 1.0 / 60.0
        dt = elapsed - self._elapsed
        self._elapsed = elapsed
        if dt <= 0.0 or dt > 0.25:
            return 1.0 / 60.0
        return dt

    # -- world index ----------------------------------------------------
    def _index(self, world):
        if self._index_world is world and self._index_cache is not None:
            return self._index_cache
        crates, machines = {}, {}
        for station in world.stations:
            if station.stype == "crate":
                crates[station.dispense] = station
            else:
                machines.setdefault(station.stype, station)
        self._index_world = world
        self._index_cache = {"crates": crates, "machines": machines}
        return self._index_cache

    # -- mission bookkeeping --------------------------------------------
    def _sweep(self, scene, dt):
        world = scene.world
        player = world.player
        keep = []
        for dish, left in list(self.cool.items()):
            left -= dt
            if left <= 0.0:
                del self.cool[dish]
            else:
                self.cool[dish] = left
        for mission in self.missions:
            mission.age += dt
            self._advance(world, mission)
            if mission.finished:
                self._release(mission)
                if not keep:
                    self.idle_left = max(self.idle_left, float(self.params["idle_wait"]))
                continue
            stuck = float(self.params.get("stuck", 30.0))
            if mission.age - mission.last_progress > stuck:
                # Wedged: its item was lost, or a machine got jammed by a dish
                # nobody wants any more.  Drop the whole mission - keeping it
                # alive only holds the machines the rest of the round needs.
                self._release(mission)
                self.cool[mission.dish] = float(self.params.get("cooldown", 12.0))
                continue
            keep.append(mission)
        self.missions = keep
        self.missions.sort(key=lambda m: self._urgency(world, m))
        if self.pre is not None:
            self.pre.age += dt
            self._advance(world, self.pre)
            if self.pre.finished:
                self._release(self.pre)
                self.pre = None
        if player.hand is None:
            self.hand_time = 0.0
        else:
            self.hand_time += dt
        self._spawn(scene)

    def _live(self):
        """Tickets plus the pre-steamed rice, which has no ticket yet."""
        return self.missions + [self.pre] if self.pre is not None else self.missions

    def _release(self, mission):
        for station in list(self.reserved):
            if self.reserved[station] is mission:
                del self.reserved[station]

    def _urgency(self, world, mission):
        best = 1e9
        for order in world.orders.active:
            if order.dish_id == mission.dish:
                best = min(best, order.time_left)
        return best

    def _advance(self, world, mission):
        for phase in mission.phases:
            if phase.done:
                continue
            if any(not dep.done for dep in phase.deps):
                continue
            guard = 0
            while phase.i < len(phase.steps) and guard < 12:
                guard += 1
                if self._status(world, phase.steps[phase.i]) != DONE:
                    break
                phase.i += 1
            if phase.i >= len(phase.steps):
                phase.done = True
                mission.last_progress = mission.age
                # The machine is free the moment this phase has used it, so a
                # second fried rice can start steaming while the first is in
                # the wok instead of waiting for the whole ticket.
                for station in phase.machines:
                    if self.reserved.get(station) is mission:
                        del self.reserved[station]

    def _preheat(self, scene):
        """Steam the next rice before its ticket lands: the steamer is the slow half."""
        if self.pre is not None or not float(self.params.get("preheat", 0.0)):
            return
        world = scene.world
        steam = self._index(world)["machines"].get("steamer")
        if steam is None or steam.phase != IDLE or steam.slot is not None:
            return
        if id(steam) in {id(station) for station in self.reserved}:
            return                    # a ticket is already on its way there
        phases = self._instantiate(scene, "rice_steamed", keep=-1)
        if not phases:
            return
        self.pre = Mission("rice_steamed", phases, None)

    def _spawn(self, scene):
        world = scene.world
        self._preheat(scene)
        limit = max(1, min(int(self.params["lookahead"]), int(self.params["max_orders"])))
        if len(self.missions) >= limit:
            return
        cap = limit + int(self.params.get("flex", 0))
        if len(self.missions) >= cap:
            return
        owners = {id(station) for station in self.reserved}
        rank = []
        for order in world.orders.active:
            if order.state != "active" or order.dish_id in self.cool:
                continue
            if any(m.tag is order for m in self.missions):
                continue                # this very ticket is already cooking
            phases = self._instantiate(scene, order.dish_id)
            if phases is None:
                continue
            machines = {id(station) for phase in phases if not phase.done
                        for station in phase.machines}
            clash = len(machines & owners)
            twin = sum(1 for m in self.missions if m.dish == order.dish_id)
            # Urgency first, but a ticket that would queue behind work already
            # in flight waits: one machine cooks one dish, and a second ticket
            # for it only idles the cook while the first one waits on a timer.
            weight = float(self.params.get("clash", 11.0))
            rank.append((order.time_left + clash * weight + twin * 16.0, order, phases))
        rank.sort(key=lambda row: row[0])
        for score, order, phases in rank:
            if len(self.missions) >= cap:
                return
            self.missions.append(Mission(order.dish_id, phases, order))

    def _instantiate(self, scene, dish_id, keep=None):
        spec = dish_spec(dish_id)
        if not spec:
            return None
        if keep is not None:
            spec = spec[:keep]
        index = self._index(scene.world)
        live, phases = {}, []
        for piece in spec:
            steps = []
            for kind, stype, item in piece.steps:
                if kind == "fetch":
                    station = index["crates"].get(item)
                else:
                    station = index["machines"].get(stype)
                if station is None:
                    return None
                steps.append(Step(kind, station, item))
            for here, later in zip(steps, steps[1:]):
                here.nxt = later
            phase = Phase(steps, [live[id(dep)] for dep in piece.deps if id(dep) in live])
            phases.append(phase)
            live[id(piece)] = phase
        return phases

    # -- legality -------------------------------------------------------
    def _status(self, world, step):
        hand = world.player.hand
        station = step.station
        kind = step.kind
        if kind == "fetch":
            if hand is not None and hand.item_id == step.item:
                return DONE
            if hand is not None:
                return BLOCKED
            if step.nxt is not None and not self._deliverable(world, step.nxt):
                return BLOCKED      # one hand: carry nothing we cannot hand over
            return TODO
        if kind == "load":
            if station.slot is not None and station.slot.item_id == step.item:
                return DONE
            rule = interaction.transform_for(station.stype, step.item)
            if (station.slot is not None and rule is not None
                    and station.slot.item_id == rule.get("output")):
                return DONE         # someone already cooked this half
            if station.phase != IDLE or hand is None:
                return BLOCKED
            if hand.item_id != step.item or not can_feed(station, step.item):
                return BLOCKED
            return TODO
        if kind == "add":
            if station.phase == ADD and station.pending:
                if station.pending[0] == step.item:
                    if hand is not None and hand.item_id == step.item:
                        return TODO
                    return BLOCKED        # go and fetch it
                if step.item in station.pending:
                    return BLOCKED        # another add goes in first
                return DONE               # this one is already in the pot
            if station.phase in (COOK, READY):
                return DONE               # the last add landed and it started
            return BLOCKED                # the base has not been loaded yet
        if kind == "chop":
            if station.phase == PREP:
                return TODO if hand is None else BLOCKED
            return DONE
        if kind == "take":
            if hand is not None and hand.item_id == step.item:
                return DONE
            if station.phase == READY:
                if hand is not None:
                    return BLOCKED
                if step.nxt is not None and not self._deliverable(world, step.nxt):
                    # Grabbing now would strand the item in our only hand: the
                    # machine that wants it is busy, and a full hand cannot
                    # clear the machine it came from either.
                    return BLOCKED
                return TODO
            if station.phase in (COOK, PREP, ADD):
                return BLOCKED
            return DONE
        if kind == "serve":
            if hand is None:
                return DONE
            if not hand.is_dish or world.orders is None:
                return BLOCKED
            return TODO if world.orders.match(hand.item_id) is not None else BLOCKED
        if kind == "trash":
            return TODO if hand is not None else DONE
        return BLOCKED

    def _deliverable(self, world, step):
        """Would this step take the item right now, were it already in hand?"""
        station = step.station
        if step.kind == "load":
            return station.phase == IDLE and can_feed(station, step.item)
        if step.kind == "add":
            return (station.phase == ADD and bool(station.pending)
                    and station.pending[0] == step.item)
        if step.kind == "serve":
            return (world.orders is not None
                    and world.orders.match(step.item) is not None)
        return True

    # -- choosing -------------------------------------------------------
    def _choose(self, world):
        hand = world.player.hand
        if hand is not None and self._junk(world, hand):
            trash = self._index(world)["machines"].get("trash")
            if trash is not None:
                step = Step("trash", trash)
                return Phase([step]), step
        legal, burning = [], []
        for mission in self._live():
            for phase in mission.phases:
                if phase.done or any(not dep.done for dep in phase.deps):
                    continue
                step = phase.current()
                if step is None:
                    continue
                if self._status(world, step) != TODO:
                    continue
                owner = self.reserved.get(step.station)
                if owner is not None and owner is not mission:
                    continue            # someone else got there first
                legal.append((phase, mission, step))
                if (step.kind == "take" and hand is None
                        and step.station.phase == READY
                        and step.station.defn.get("heat")):
                    burning.append((step.station.burn, phase, mission, step))
        if not legal:
            return None
        urgent = float(self.params["burn_urgent"])
        if burning:
            burning.sort(key=lambda row: -row[0])
            burn, phase, mission, step = burning[0]
            if burn >= urgent:
                return self._claim(phase, mission, step)
        skip = float(self.params["skip"])
        if skip > 0.0 and len(legal) > 1 and self.rng.random() < skip:
            return self._claim(*legal[1 + self.rng.randrange(len(legal) - 1)])
        if float(self.params.get("nearest", 0.0)) > 0.0:
            legal.sort(key=lambda row: self._near(world, row[2]))
        return self._claim(*legal[0])

    def _near(self, world, step):
        """How far this station is, in tiles, from where the cook stands."""
        grid = nav.grid_for(world)
        here = grid.cell(world.player.foot.center)
        foot = step.station.foot
        cell = grid.cell((foot.centerx, foot.centery))
        return abs(here[0] - cell[0]) + abs(here[1] - cell[1])

    def _claim(self, phase, mission, step):
        """Nobody else may touch this station until the phase is done with it."""
        for station in (phase.machines or (step.station,)):
            if station.stype in MACHINES:
                self.reserved.setdefault(station, mission)
        return phase, step

    def _junk(self, world, hand):
        """Is what we hold useless to every ticket still in flight?"""
        if hand.is_dish:
            if world.orders is not None and world.orders.match(hand.item_id) is not None:
                return False
        for mission in self.missions:
            for phase in mission.phases:
                if phase.done:
                    continue
                for step in phase.steps[phase.i:]:
                    if step.kind in ("load", "add") and step.item == hand.item_id:
                        return self.hand_time > float(self.params["hand_timeout"])
        return True

    # -- doing ----------------------------------------------------------
    def _act(self, scene, pick, intent):
        phase, step = pick
        world = scene.world
        player = world.player
        grid = nav.grid_for(world)
        station = step.station
        here = grid.cell(player.foot.center)
        goal = self._stand(grid, station, here)
        if goal is None:
            return
        centre = grid.center(goal)
        self.job = "%s %s" % (step.kind, getattr(station, "label", station.stype))
        if here != goal:
            move = self._steer(grid, player, here, goal)
            if move is not None:
                intent.mx, intent.my, intent.sprint = move
            return
        gap_x = centre[0] - player.foot.centerx
        gap_y = centre[1] - player.foot.centery
        slack = float(self.params["turn_slack"])
        if abs(gap_x) > slack or abs(gap_y) > slack:
            intent.mx = 0 if abs(gap_x) <= 2 else (1 if gap_x > 0 else -1)
            intent.my = 0 if abs(gap_y) <= 2 else (1 if gap_y > 0 else -1)
            return
        cell = grid.cell((station.foot.centerx, station.foot.centery))
        facing = (cell[0] - here[0], cell[1] - here[1])
        if abs(facing[0]) + abs(facing[1]) != 1:
            sx = station.foot.centerx - player.foot.centerx
            sy = station.foot.centery - player.foot.centery
            if abs(sx) > abs(sy):
                facing = (1 if sx > 0 else -1, 0)
            else:
                facing = (0, 1 if sy > 0 else -1)
        if tuple(player.facing) != facing:
            intent.mx, intent.my = facing
            return
        if interaction.find_target(world, player) is not station:
            return
        intent.interact = True
        dwell = float(self.params["dwell"])
        if dwell > 0.0:
            self.pause = dwell

    def _stand(self, grid, station, here):
        """The tile to work this station from, locked while we walk to it."""
        key = id(station)
        if self._goal is not None and self._goal[0] == key:
            cell = self._goal[1]
            if grid.walkable(cell):
                return cell
        cell = grid.stand(station, prefer_from=here)
        if cell is None:
            return None
        self._goal = (key, cell)
        return cell

    def _steer(self, grid, player, here, goal):
        path = self._route(grid, here, goal)
        if not path:
            return None
        wx, wy = grid.center(path[0])
        gap_x = wx - player.foot.centerx
        gap_y = wy - player.foot.centery
        mx = 0 if abs(gap_x) <= 3 else (1 if gap_x > 0 else -1)
        my = 0 if abs(gap_y) <= 3 else (1 if gap_y > 0 else -1)
        if not mx and not my:
            mx = 1 if gap_x > 0 else (-1 if gap_x < 0 else 0)
            my = 1 if gap_y > 0 else (-1 if gap_y < 0 else 0)
        sprint = bool(self.params["sprint"]) and abs(gap_x) + abs(gap_y) > 24
        return mx, my, sprint

    def _route(self, grid, here, goal):
        key = (here, goal)
        if self._path_key == key:
            return self._path
        path = grid.path(here, goal)
        self._path_key = key
        self._path = path or []
        return self._path

    # -- waiting --------------------------------------------------------
    def _drift(self, scene, intent):
        """Nothing legal: stand where the next timer will need us."""
        world = scene.world
        player = world.player
        best = None
        for mission in self.missions:
            for phase in mission.phases:
                if phase.done or any(not dep.done for dep in phase.deps):
                    continue
                step = phase.current()
                if step is None or step.kind != "take":
                    break
                station = step.station
                if station.phase == COOK:
                    eta = max(0.0, station.duration - station.timer)
                elif station.phase == READY:
                    eta = -1.0
                else:
                    eta = 0.0
                if best is None or eta < best[0]:
                    best = (eta, station)
                break
        if best is None:
            return
        grid = nav.grid_for(world)
        here = grid.cell(player.foot.center)
        station = best[1]
        if self._goal is None or self._goal[0] != id(station):
            cell = grid.stand(station, prefer_from=here)
            if cell is None:
                return
            self._goal = (id(station), cell)
        goal = self._goal[1]
        if here == goal:
            return
        if abs(here[0] - goal[0]) + abs(here[1] - goal[1]) <= 1:
            return
        move = self._steer(grid, player, here, goal)
        if move is not None:
            intent.mx, intent.my, intent.sprint = move

    # -- introspection --------------------------------------------------
    def state(self):
        """Small dict for the demo overlay and for debugging."""
        heads = []
        for mission in self.missions:
            for phase in mission.phases:
                if phase.done or any(not dep.done for dep in phase.deps):
                    continue
                step = phase.current()
                if step is not None:
                    heads.append("%s:%s/%s" % (mission.dish, step.kind,
                                               getattr(step.station, "label", "")))
                break
        return {"profile": self.profile, "job": self.job,
                "missions": len(self.missions), "heads": heads,
                "reserved": sorted(s.stype for s in self.reserved)}
