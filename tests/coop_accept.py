"""Acceptance for the two-cook slice: A1-A7, measured on the real scene.

These are the checks the plan promised; each prints its number, so a run is also
the record in the docs.

  python tests/coop_accept.py            # full: A1, A6 take ~40 s of CPU
  python tests/coop_accept.py --quick    # skip the 180 s rounds
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import types

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import profile
from core.input import Intent
from game.systems import ai, difficulty, interaction, nav, ordering
from scenes.game import GameScene

DT = 1.0 / 60.0
QUICK = False

#: solo strong, hard, seeds 1-5, 180 s -- the shipped benchmark baseline
SOLO_STRONG = 806.8
SOLO_RELAXED = 381.2


class FakeApp:
    def __init__(self, coop=False, policy="backlog", helper="helper"):
        self.scene = None
        self.running = True
        self.difficulty = "hard"
        self.coop = coop
        self.helper_profile = helper
        self.helper_policy = policy

    def switch(self, scene):
        self.scene = scene


def scene_for(seed=7, coop=True, policy="backlog", duration=180.0):
    app = FakeApp(coop=coop, policy=policy)
    scene = GameScene(app, "hard")
    scene.world.orders = ordering.OrderBoard(
        seed=seed, cap=5, duration=duration,
        patience_scale=difficulty.patience_scale("hard"),
        interval_scale=difficulty.spawn_scale("hard"))
    scene.duration = duration
    return scene


def play(scene, seconds, brain=None, on_frame=None):
    for _ in range(int(seconds / DT)):
        intent = brain.think(scene) if brain is not None else Intent()
        scene.update(DT, intent)
        if on_frame is not None:
            on_frame(scene)


def station(world, stype):
    return next(s for s in world.stations if s.stype == stype)


def stand_at(scene, actor, target):
    """Put a body on the tile it would work this station from, facing it."""
    world, grid = scene.world, nav.grid_for(scene.world)
    here = grid.cell(actor.foot.center)
    cell = grid.stand(target, prefer_from=here)
    x, y = grid.center(cell)
    actor.foot.center = (x, y)
    bc = grid.cell(target.foot.center)
    dx, dy = bc[0] - cell[0], bc[1] - cell[1]
    if abs(dx) + abs(dy) != 1:
        dx, dy = (1 if target.foot.centerx > actor.foot.centerx else -1, 0)
    actor.facing = (dx, dy)
    return cell


def mission_of(actor):
    return types.SimpleNamespace(brain=types.SimpleNamespace(actor=actor))


def round_stars(seed, coop=False, player="strong"):
    scene = scene_for(seed=seed, coop=coop, duration=180.0)
    brain = ai.Brain(player, actor=scene.player, board=scene.world.tasks)
    play(scene, 180.0, brain)
    return scene.world.score.final_stars()


# -- A1 -----------------------------------------------------------------
def case_a1():
    seconds = 20.0 if QUICK else 180.0
    scene = scene_for(seed=7)
    play(scene, seconds)
    served = len(scene.world.orders.served)
    problems = scene.world.validate()
    assert problems == [], problems[:2]
    if not QUICK:
        assert served >= 8, "helper served only %d tickets on seed 7" % served
    return "player idle %.0f s -> %d tickets served, validate clean" % (seconds, served)


# -- A2 -----------------------------------------------------------------
def case_a2():
    """A player who walks away must not leave a wall of dying tickets."""
    seconds = 40.0 if QUICK else 180.0
    stats = {}
    for name, coop in (("solo", False), ("coop", True)):
        scene = scene_for(seed=7, coop=coop, duration=seconds)
        queues = []
        play(scene, seconds, None, lambda s: queues.append(len(s.world.orders.queue)))
        board = scene.world.orders
        half = len(queues) // 2
        stats[name] = {
            "peak": max(queues), "first": max(queues[:half] or [0]),
            "last": max(queues[half:] or [0]),
            "failed": len(board.failed), "served": len(board.served),
        }
    solo, coop = stats["solo"], stats["coop"]
    if not QUICK:
        assert solo["peak"] > 0, "no backlog formed even with nobody cooking"
        assert coop["failed"] < solo["failed"], stats
        assert coop["last"] <= coop["peak"], stats
    return ("idle player: queue peak solo %d / coop %d, failed solo %d / coop %d, "
            "served solo %d / coop %d" % (solo["peak"], coop["peak"], solo["failed"],
                                          coop["failed"], solo["served"], coop["served"]))


# -- A3 -----------------------------------------------------------------
def case_a3():
    scene = scene_for()
    board_station = station(scene.world, "board")
    world = scene.world
    world.give_to_hand(scene.player, world.new_item("veg"))
    stand_at(scene, scene.player, board_station)
    scene.target = board_station
    touched = []
    original = interaction.interact_with_detail

    def watched(w, actor, target, *args, **kwargs):
        if actor is scene.helper.actor and target is board_station:
            touched.append(1)
        return original(w, actor, target, *args, **kwargs)

    interaction.interact_with_detail = watched
    try:
        play(scene, 3.0)
    finally:
        interaction.interact_with_detail = original
    owner = world.tasks.station_owner(board_station)
    assert not touched, "helper worked the board the player is chopping on"
    assert not hasattr(owner, "brain"), "helper leased the player's board"
    return "3 s on the board: %d helper actions there, lease %r" % (
        len(touched), "player" if owner == "player" else owner)


# -- A4 -----------------------------------------------------------------
def case_a4():
    scene = scene_for()
    hero = ai.Brain("strong", actor=scene.player, board=scene.world.tasks)
    seen = {}
    broken = []

    def check(s):
        for brain in (hero, scene.helper.brain):
            for mission in brain.missions:
                if mission.tag is None:
                    continue
                key = id(mission.tag)
                owner = seen.setdefault(key, id(brain))
                if owner != id(brain):
                    broken.append(mission.tag.dish_id)

    play(scene, 60.0, hero, check)
    problems = scene.world.validate()
    assert not broken, "two brains claimed the same ticket: %s" % broken[:3]
    assert problems == [], problems[:2]
    return "%d tickets over 60 s, one owner each, validate clean" % len(seen)


# -- A5 -----------------------------------------------------------------
def case_a5():
    scene = scene_for()
    world = scene.world
    steamer = station(world, "steamer")
    steamer.phase = "cook"
    steamer.slot = world.new_item("rice")
    steamer.timer = 1.0
    steamer.duration = 6.0
    lease = mission_of(scene.helper.actor)
    world.tasks.claim_station(steamer, lease)
    stand_at(scene, scene.player, steamer)
    assert interaction.find_target(world, scene.player) is steamer
    event, detail = interaction.interact_with_detail(world, scene.player, steamer)
    assert event in ("reject", "noop"), event
    assert "帮厨" in detail, detail
    world.tasks.release_owner(lease)
    return "F on the helper's steamer -> %s: %s" % (event, detail)


# -- A6 -----------------------------------------------------------------
def case_a6():
    if QUICK:
        return "skipped (--quick)"
    seeds = (1, 2, 3, 4, 5)
    strong_solo = [round_stars(s) for s in seeds]
    strong_coop = [round_stars(s, coop=True) for s in seeds]
    relaxed_solo = [round_stars(s, player="relaxed") for s in seeds]
    relaxed_coop = [round_stars(s, coop=True, player="relaxed") for s in seeds]
    m = statistics.mean
    assert abs(m(strong_solo) - SOLO_STRONG) < 0.5, strong_solo
    assert m(strong_coop) >= m(strong_solo) - 1.0, (strong_coop, strong_solo)
    assert m(relaxed_coop) > m(relaxed_solo), (relaxed_coop, relaxed_solo)
    return ("strong solo %.1f / coop %.1f (%+.1f), relaxed solo %.1f / coop %.1f (%+.1f)"
            % (m(strong_solo), m(strong_coop), m(strong_coop) - m(strong_solo),
               m(relaxed_solo), m(relaxed_coop), m(relaxed_coop) - m(relaxed_solo)))


# -- A7 -----------------------------------------------------------------
def case_a7():
    """A coop round must count itself and nothing else -- and leave the save as found."""
    saved = None
    if os.path.exists(profile.PATH):
        with open(profile.PATH, "rb") as handle:
            saved = handle.read()
    try:
        data_before = profile.load()
        best_before = profile.best("hard")
        assert profile.DEFAULT_SETTINGS["coop"] is False, profile.DEFAULT_SETTINGS
        profile.record_coop()
        data_after = profile.load()
        assert profile.best("hard") == best_before, "a coop round touched the record"
        assert data_after["coop_runs"] == data_before["coop_runs"] + 1, data_after["coop_runs"]
        assert data_after["unlocked"] == data_before["unlocked"], "a coop round unlocked a level"
    finally:
        if saved is not None:
            with open(profile.PATH, "wb") as handle:
                handle.write(saved)
    return "coop defaults off, record_coop only counts, save untouched"


CASES = (
    ("A1 absent player", case_a1),
    ("A2 backlog", case_a2),
    ("A3 yields board", case_a3),
    ("A4 one owner", case_a4),
    ("A5 tells you why", case_a5),
    ("A6 throughput", case_a6),
    ("A7 no records", case_a7),
)


def main(argv=None):
    global QUICK
    parser = argparse.ArgumentParser(description="two-cook acceptance")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args(argv)
    QUICK = args.quick
    pygame.init()
    pygame.display.set_mode((320, 180))
    failures = 0
    for name, case in CASES:
        try:
            note = case()
        except AssertionError as exc:
            failures += 1
            print("  FAIL %-18s %s" % (name, exc))
        except Exception as exc:  # noqa: BLE001 - report, do not hide
            failures += 1
            print("  ERROR %-17s %s: %s" % (name, type(exc).__name__, exc))
        else:
            print("  ok   %-18s %s" % (name, note))
    pygame.quit()
    print("COOP: %s (%d/%d)" % ("FAIL" if failures else "PASS",
                                len(CASES) - failures, len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
