"""The second cook: autonomy, manners and the lease rules around it.

Every case drives the real GameScene, so what passes here is what the game does.

  python tests/helper.py
"""
from __future__ import annotations

import os
import sys
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core.input import Intent
from game.systems import ai, difficulty, interaction, ordering
from scenes.game import GameScene

DT = 1.0 / 60.0


class FakeApp:
    def __init__(self, coop=False, profile="helper", policy="backlog"):
        self.scene = None
        self.running = True
        self.difficulty = "hard"
        self.coop = coop
        self.helper_profile = profile
        self.helper_policy = policy

    def switch(self, scene):
        self.scene = scene


def scene_for(seed=7, coop=True, policy="backlog", profile="helper"):
    app = FakeApp(coop=coop, profile=profile, policy=policy)
    scene = GameScene(app, "hard")
    scene.world.orders = ordering.OrderBoard(
        seed=seed, cap=5, duration=180.0,
        patience_scale=difficulty.patience_scale("hard"),
        interval_scale=difficulty.spawn_scale("hard"))
    scene.duration = 180.0
    return scene


def fake_mission(actor):
    """A lease holder shaped like a Mission: only .brain.actor is ever read."""
    return types.SimpleNamespace(brain=types.SimpleNamespace(actor=actor))


def _pressed_helper():
    """A frame where the player tapped Y."""
    intent = Intent()
    intent.helper = True
    return intent


def helper_actions(scene, seconds):
    """Run the scene and count how many interactions the helper performs."""
    helper = scene.helper
    original = interaction.interact_with_detail
    seen = [0]

    def counted(world, actor, target, *args, **kwargs):
        if actor is helper.actor:
            seen[0] += 1
        return original(world, actor, target, *args, **kwargs)

    interaction.interact_with_detail = counted
    try:
        play(scene, seconds)
    finally:
        interaction.interact_with_detail = original
    return seen[0]


def play(scene, seconds, brain=None):
    frames = int(seconds / DT)
    for _ in range(frames):
        intent = brain.think(scene) if brain is not None else Intent()
        scene.update(DT, intent)


# -- 1. it works on its own --------------------------------------------
def case_autonomous():
    scene = scene_for()
    play(scene, 60.0)
    board = scene.world.orders
    served = len(board.served)
    moved = scene.helper.actor.foot.x != scene.world.spawn_x if hasattr(scene.world, "spawn_x") else True
    problems = scene.world.validate()
    assert served >= 3, "helper served %d tickets in 60 s" % served
    assert problems == [], problems
    return "served %d tickets alone, validate clean" % served


# -- 2. one ticket, one owner ------------------------------------------
def case_no_duplicate_claim():
    scene = scene_for()
    board = scene.world.tasks
    orders = scene.world.orders
    hero = ai.Brain("strong", actor=scene.player, board=board)
    play(scene, 12.0, hero)
    helper = scene.helper.brain
    tags = [m.tag for m in hero.missions if m.tag is not None]
    tags += [m.tag for m in helper.missions if m.tag is not None]
    assert len(tags) == len(set(id(t) for t in tags)), "two missions share a ticket"
    order = ordering.Order("salad")      # a fresh ticket nobody has seen yet
    mine, theirs = fake_mission(scene.player), fake_mission(scene.helper.actor)
    assert board.claim_order(order, mine) is True
    assert board.claim_order(order, theirs) is False, "a second cook claimed a taken ticket"
    assert board.claim_order(order, mine) is True, "the owner cannot refresh its own lease"
    board.release_order(order)
    return "claims are exclusive, budgets disjoint"


# -- 3. it steps off a station the player aims at -----------------------
def case_yields_to_player():
    scene = scene_for()
    play(scene, 8.0)
    helper = scene.helper
    station = next(s for s in scene.world.stations if s.stype == "board")
    mission = fake_mission(helper.actor)
    helper.brain.reserved[station] = mission
    scene.world.tasks.claim_station(station, mission)
    scene.world.tasks.note_player(station=station)
    helper.think(scene)
    assert station not in helper.brain.reserved, "helper kept a station the player aimed at"
    assert scene.world.tasks.station_owner(station) is not mission
    return "released the aimed station"


# -- 4. the player still gets told why ---------------------------------
def case_contention_feedback():
    scene = scene_for()
    station = next(s for s in scene.world.stations if s.stype == "board")
    station.phase = "prep"
    station.slot = None
    mission = fake_mission(scene.helper.actor)
    scene.world.tasks.claim_station(station, mission)
    event, detail = interaction.interact_with_detail(scene.world, scene.player, station)
    assert event in ("reject", "noop"), event
    assert "帮厨" in detail, detail
    scene.world.tasks.release_owner(mission)
    return "rejected with reason: %s" % detail


# -- 5. both cooks can carry -------------------------------------------
def case_both_hands():
    scene = scene_for()
    player, helper = scene.world.player, scene.helper.actor
    player.hand = scene.world.new_item("rice")
    helper.hand = scene.world.new_item("veg")
    problems = scene.world.validate()
    assert problems == [], problems
    assert player.hand is not None and helper.hand is not None
    return "two hands, one item each, validate clean"


# -- 6. Y sends it home ------------------------------------------------
def case_pause_switch():
    scene = scene_for()
    play(scene, 5.0)
    helper = scene.helper
    body = helper.actor
    scene.update(DT, _pressed_helper())
    assert helper.paused is True
    before = (body.foot.x, body.foot.y)
    play(scene, 3.0)
    after = (body.foot.x, body.foot.y)
    assert before == after, "a paused helper moved"
    scene.update(DT, _pressed_helper())
    assert helper.paused is False
    # It may legitimately wait out an 8 s steam timer, so give it a real window.
    actions = helper_actions(scene, 15.0)
    assert actions > 0, "helper never came back to work after resuming"
    return "paused still, back to work after the second tap (%d actions)" % actions


# -- 7. assist only takes tickets that are failing ---------------------
def case_assist_only_urgent():
    scene = scene_for(policy="assist")
    orders = scene.world.orders
    order = ordering.Order("salad")
    order.time_left = order.patience * 0.95
    orders.active.append(order)
    helper = scene.helper
    helper.note_player(1e9)          # player is present: no solo takeover
    play(scene, 2.0)
    taken = any(m.tag is order for m in helper.brain.missions)
    assert not taken, "assist took a fresh ticket"
    order.time_left = order.patience * 0.25
    play(scene, 4.0)
    taken = any(m.tag is order for m in helper.brain.missions)
    assert taken, "assist ignored a failing ticket"
    return "fresh ticket left alone, failing ticket taken"


# -- 8. long round stays consistent ------------------------------------
def case_soak():
    scene = scene_for()
    hero = ai.Brain("strong", actor=scene.player, board=scene.world.tasks)
    problems = []
    for frame in range(2000):
        scene.update(DT, hero.think(scene))
        if frame % 200 == 0:
            problems.extend(scene.world.validate())
    problems.extend(scene.world.validate())
    assert problems == [], problems[:3]
    return "2000 frames, validate clean"


CASES = (
    ("autonomous", case_autonomous),
    ("no duplicate claim", case_no_duplicate_claim),
    ("yields to player", case_yields_to_player),
    ("contention feedback", case_contention_feedback),
    ("both hands", case_both_hands),
    ("pause switch", case_pause_switch),
    ("assist only urgent", case_assist_only_urgent),
    ("soak", case_soak),
)


def main():
    pygame.init()
    pygame.display.set_mode((320, 180))
    failures = 0
    for name, case in CASES:
        try:
            note = case()
        except AssertionError as exc:
            failures += 1
            print("  FAIL %-20s %s" % (name, exc))
        except Exception as exc:  # noqa: BLE001 - report, do not hide
            failures += 1
            print("  ERROR %-19s %s: %s" % (name, type(exc).__name__, exc))
        else:
            print("  ok   %-20s %s" % (name, note))
    pygame.quit()
    print("HELPER: %s (%d/%d)" % ("FAIL" if failures else "PASS",
                                  len(CASES) - failures, len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
