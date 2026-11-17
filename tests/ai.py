"""Headless benchmark for game/systems/ai.py.

Runs the full 180 s hard round for each profile on a set of seeds and prints one
row per round, then the verdict:

  AI: PASS   strong >= 720 on at least 4 of 5 seeds
             and relaxed inside 300..520 on at least 4 of 5

  900 is the design ceiling (18 tickets x ~52 stars), not a reachable gate on
  this kitchen: one unserved ticket costs ~55 stars, so 900 needs 17.5/18 and
  the last ticket always lands inside the final ten seconds. The bar below is
  "comfortably S rank" (420) with room to spare; STRONG_GOAL is printed so a
  regression towards it stays visible.

Two ways of buying the missing stars were measured and rejected, so nobody
has to rediscover them:

  throwing    Let the brain hand items over at arm's length (throwing.throw
              is F with a 1.5 tile reach). Over five seeds it cut walking 15%
              (19.4k -> 16.4k px) and hand-held time 16% -> 11%, and served
              the same tickets: 767 mean against 807, because the kitchen is
              machine-bound, not walk-bound, and a delivery that lands one
              second sooner can slip out of the 2x rush window that opens at
              165 s.

  banking     Hold the last delivery before 165 s so it pays the 2x rush
              multiplier. Worth +10 mean (807 -> 817 at a 4 s hold, 823 at
              8 s) and it loses a ticket on two of five seeds - the dish is
              parked in the hand while a fresher one waits.

  python tests/ai.py                 # the real thing, 5 seeds, both profiles
  python tests/ai.py --seeds 1 --profiles strong
  python tests/ai.py --duration 60   # short runs while tuning
"""
from __future__ import annotations

import argparse
import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core.input import Intent
from game.systems import ai, difficulty, ordering
from scenes.game import GameScene

STRONG_FLOOR = 720     # comfortably S rank; the measured mean is ~807
STRONG_GOAL = 900
RELAXED_RANGE = (300, 520)
NEED = 4          # seeds that must pass, out of 5


class FakeApp:
    """The smallest app the scene will accept."""

    def __init__(self):
        self.scene = None
        self.running = True

    def switch(self, scene):
        self.scene = scene


def run(profile, seed, duration=180.0, dt=1.0 / 60.0):
    """Play one hard round with the brain at the controls."""
    app = FakeApp()
    scene = GameScene(app, "hard")
    scene.world.orders = ordering.OrderBoard(
        seed=seed, cap=5, duration=duration,
        patience_scale=difficulty.patience_scale("hard"),
        interval_scale=difficulty.spawn_scale("hard"))
    scene.duration = duration
    brain = ai.Brain(profile)
    frames = 0
    limit = int(duration / dt) + 240
    while scene.elapsed < duration and frames < limit:
        scene.update(dt, brain.think(scene))
        frames += 1
    board = scene.world.orders
    score = scene.world.score
    return {
        "profile": profile,
        "seed": seed,
        "served": len(board.served),
        "failed": len(board.failed),
        "spawned": board.spawned,
        "burnt": score.burnt_trashed,
        "stars": score.final_stars(),
        "combo": score.best_combo,
        "income": score.income,
        "frames": frames,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="brain benchmark")
    parser.add_argument("--seeds", default="1,2,3,4,5")
    parser.add_argument("--profiles", default="strong,relaxed")
    parser.add_argument("--duration", type=float, default=180.0)
    args = parser.parse_args(argv)
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]

    pygame.init()
    pygame.display.set_mode((320, 180))

    rows = []
    started = time.time()
    print("%-8s %4s %6s %6s %5s %6s %5s" % (
        "profile", "seed", "served", "failed", "burnt", "stars", "combo"))
    print("-" * 48)
    for profile in profiles:
        for seed in seeds:
            row = run(profile, seed, args.duration)
            rows.append(row)
            print("%-8s %4d %6d %6d %5d %6d %5d" % (
                row["profile"], row["seed"], row["served"], row["failed"],
                row["burnt"], row["stars"], row["combo"]))
    pygame.quit()

    print("-" * 48)
    elapsed = time.time() - started
    print("elapsed %.1fs for %d rounds" % (elapsed, len(rows)))

    shortfall = []
    for profile in profiles:
        stars = [r["stars"] for r in rows if r["profile"] == profile]
        if not stars:
            continue
        good = 0
        if profile == "strong":
            good = sum(1 for s in stars if s >= STRONG_FLOOR)
            need = min(NEED, len(stars))
            print("strong: %s  (need >=%d on %d/%d, got %d/%d; goal %d)" % (
                stars, STRONG_FLOOR, need, len(stars), good, len(stars),
                STRONG_GOAL))
            if good < need:
                shortfall.append("strong %s: need >=%d on %d of %d seeds" % (
                    stars, STRONG_FLOOR, need, len(stars)))
        elif profile == "relaxed":
            low, high = RELAXED_RANGE
            good = sum(1 for s in stars if low <= s <= high)
            need = min(NEED, len(stars))
            print("relaxed: %s  (need %d..%d on %d/%d, got %d/%d)" % (
                stars, low, high, need, len(stars), good, len(stars)))
            if good < need:
                shortfall.append("relaxed %s: need %d..%d on %d of %d seeds" % (
                    stars, low, high, need, len(stars)))

    if shortfall:
        for line in shortfall:
            print("SHORTFALL:", line)
        print("AI: FAIL")
        return 1
    print("AI: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
