"""The second cook: an autonomous helper (灶罐) that runs its own tickets.

The helper is not a second set of rules.  It is the same Brain the benchmark
runs, driving a second body through the shared TaskBoard, with one extra layer
of manners:

  * it yields any station the player is aiming at (the board refreshes that
    claim every frame), so the player never fights it for the oven;
  * it only *offers* to help: the player's tickets are never taken away;
  * once the player has not touched a key for AWAY_AFTER seconds it stops being
    a helper and just cooks, three tickets in flight - an idle player must never
    watch a stocked kitchen stand still.

Two policies, both pure parameter patches on the same planner:

  backlog  business mode - clear tickets the player has not reached yet, two in
           flight, and give up the station the player is aiming at.
  assist   battle mode - only jump in on tickets already running out of
           patience (>55% of patience spent), rescue burning plates first and
           sprint.  New tickets always belong to the player.
"""
from __future__ import annotations

from core import config
from core.input import Intent
from game.systems import ai

#: Only what "being the second cook" changes; dwell/skip/sprint stay with the
#: profile, so 学徒 and 熟手 really do move and pick differently (data/ai.json).
BACKLOG = {
    "lookahead": 2,
    "flex": 0,
    "preheat": 0,        # measured: a pre-steamed bowl blocks the steamer more
    "hand_timeout": 14.0,  # often than it saves the rice ticket
    "clash": 22.0,       # prefer tickets that want machines the other cook is not on
}

ASSIST = {
    "lookahead": 1,
    "flex": 0,
    "sprint": True,      # rescue work is worth the speed
    "burn_urgent": 2.5,
    "hand_timeout": 8.0,
}

#: assist only takes tickets this close to failing; new tickets are the player's
ASSIST_PATIENCE = 0.55

#: the player counts as "away" this long after their last input: the helper then
#: stops being a helper and runs the kitchen itself (three tickets in flight)
AWAY_AFTER = 3.0
SOLO = {"lookahead": 3, "flex": 2, "skip": 0.0, "dwell": 0.0, "sprint": True}

#: Brain.job is "<step kind> <station label>"; the chip says it in Chinese
VERBS = {"fetch": "取", "load": "放", "add": "加", "chop": "切",
         "take": "端", "serve": "送", "trash": "扔"}


class Helper:
    """Wraps one Brain with a body, a policy and a pause switch."""

    def __init__(self, actor, world, profile="helper", policy="backlog"):
        self.actor = actor
        self.policy = policy if policy in ("backlog", "assist") else "backlog"
        self.brain = ai.Brain(profile=profile, actor=actor, board=world.tasks)
        self.base = dict(self.brain.params)
        self.paused = False
        self.seen = 0.0          # last time the player did anything
        self.solo = False        # running the kitchen alone
        tuning = dict(config.TUNING["player"])
        tuning.update(config.TUNING.get("helper") or {})
        self.tuning = tuning
        self.apply_policy()

    # -- policy ---------------------------------------------------------
    def apply_policy(self, policy=None, solo=None):
        if policy is not None:
            self.policy = policy if policy in ("backlog", "assist") else self.policy
        if solo is not None:
            self.solo = bool(solo)
        patch = ASSIST if self.policy == "assist" else BACKLOG
        self.brain.params = dict(self.base)
        self.brain.params.update(patch)
        if self.solo:
            # Nobody else is working: the manners come off and the full planner
            # runs, or the kitchen idles while a perfectly good cook stands by.
            self.brain.params.update(SOLO)
        if self.policy == "assist" and not self.solo:
            self.brain.order_filter = lambda order: order.patience_ratio < ASSIST_PATIENCE
        else:
            self.brain.order_filter = None

    def set_profile(self, profile):
        table = ai.load_profiles()
        profile = profile if profile in table else "helper"
        self.brain.profile = profile
        self.base = dict(table[profile])
        self.apply_policy()

    # -- frame ----------------------------------------------------------
    def think(self, scene):
        if self.paused:
            return Intent()
        self._watch_player(scene)
        self.yield_to_player(scene.world)
        return self.brain.think(scene)

    def note_player(self, when):
        """The player touched something at scene time *when*."""
        self.seen = when

    def _watch_player(self, scene):
        away = scene.elapsed - self.seen > AWAY_AFTER
        if away != self.solo:
            self.apply_policy(solo=away)
        if not self.solo:
            # A human cannot claim a ticket the way a planner can, so the helper
            # never holds the whole board: one live ticket always stays open.
            live = len([o for o in scene.world.orders.active if o.state == "active"])
            self.brain.params["lookahead"] = max(1, min(2, live - 1))

    def yield_to_player(self, world):
        """Give back any machine the player has just aimed at."""
        station = world.tasks.player_station()
        if station is None:
            return
        held = self.brain.reserved.pop(station, None)
        if held is None:
            held = world.tasks.station_owner(station)
            # A player lease is text, not a mission: that one is not ours to drop.
            if held is None or isinstance(held, str):
                return
        world.tasks.release_station(station, held)

    # -- control --------------------------------------------------------
    def toggle(self):
        self.paused = not self.paused
        self.release()
        return self.paused

    def release(self):
        """Drop every lease this cook holds (pause, round end, scene swap)."""
        for mission in self.brain._live():
            self.brain.board.release_owner(mission)
        self.brain.reserved.clear()

    def resume(self):
        self.paused = False

    # -- introspection --------------------------------------------------
    def state(self):
        info = self.brain.state()
        info["policy"] = self.policy
        info["paused"] = self.paused
        info["profile"] = self.brain.profile
        return info

    def label(self):
        if self.paused:
            return "帮厨 · 歇着（Y 上工）"
        names = {"backlog": "补单", "assist": "辅助"}
        job = self.brain.job or "待命"
        kind, _, rest = job.partition(" ")
        job = VERBS.get(kind, kind) + rest if rest else VERBS.get(kind, job)
        return "帮厨 · %s · %s" % (names.get(self.policy, "补单"), job)
