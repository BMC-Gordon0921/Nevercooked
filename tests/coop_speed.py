"""Does the second cook actually add throughput?  Measured, not asserted.

Runs the real GameScene for each seed three ways and prints stars:

  solo    one brain at the controls (strong = the 806.8 baseline in the README)
  coop    the same brain plus the helper on the backlog policy (clear the queue)
  assist  the same brain plus the helper on the assist policy (rescue only)

The player profile matters more than the policy, so say which one you mean:
with a *strong* bot at the controls the kitchen is arrival-limited (the bot
already clears every ticket) and the helper has nothing to add; with a slow,
human-like *relaxed* bot the helper is worth a large chunk of stars.

  python tests/coop_speed.py                        # strong player, 5 seeds
  python tests/coop_speed.py --player relaxed       # human-like player
  python tests/coop_speed.py --seeds 1 --duration 60
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from game.systems import ai, difficulty, interaction, ordering
from scenes.game import GameScene

#: solo strong, hard, seeds 1-5, 180 s -- recorded before the helper existed
SOLO_BASELINE = {"strong": 806.8, "relaxed": 381.2}


class FakeApp:
    """The smallest app the scene will accept."""

    def __init__(self, coop=False, profile="helper", policy="backlog"):
        self.scene = None
        self.running = True
        self.difficulty = "hard"
        self.coop = coop
        self.helper_profile = profile
        self.helper_policy = policy

    def switch(self, scene):
        self.scene = scene


class _ServeTally:
    """Count deliveries per cook by watching the pass station."""

    def __init__(self, scene):
        self.helper = scene.helper.actor if scene.helper is not None else None
        self.own = {"player": 0, "helper": 0}
        self._original = interaction.interact_with_detail

    def __enter__(self):
        original, own = self._original, self.own

        def counted(world, actor, target, *args, **kwargs):
            if getattr(target, "stype", None) == "serve":
                own["helper" if actor is self.helper else "player"] += 1
            return original(world, actor, target, *args, **kwargs)

        interaction.interact_with_detail = counted
        return self

    def __exit__(self, *exc):
        interaction.interact_with_detail = self._original
        return False


def run(seed, coop=False, profile="helper", policy="backlog",
        player="strong", duration=180.0, dt=1.0 / 60.0):
    """Play one hard round with a brain at the controls (+ the helper)."""
    app = FakeApp(coop=coop, profile=profile, policy=policy)
    scene = GameScene(app, "hard")
    scene.world.orders = ordering.OrderBoard(
        seed=seed, cap=5, duration=duration,
        patience_scale=difficulty.patience_scale("hard"),
        interval_scale=difficulty.spawn_scale("hard"))
    scene.duration = duration
    # Both cooks must see the same leases, or the benchmark measures two brains
    # that fight over machines they each believe are free.
    brain = ai.Brain(player, actor=scene.player, board=scene.world.tasks)
    frames = 0
    limit = int(duration / dt) + 240
    tally = _ServeTally(scene)
    with tally:
        while scene.elapsed < duration and frames < limit:
            scene.update(dt, brain.think(scene))
            frames += 1
    board = scene.world.orders
    return {
        "seed": seed,
        "mode": "coop" if coop else "solo",
        "policy": policy if coop else "-",
        "served": len(board.served),
        "failed": len(board.failed),
        "spawned": board.spawned,
        "stars": scene.world.score.final_stars(),
        "frames": frames,
        "helper_serves": tally.own["helper"],
        "problems": scene.world.validate(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="coop throughput benchmark")
    parser.add_argument("--seeds", default="1,2,3,4,5")
    parser.add_argument("--duration", type=float, default=180.0)
    parser.add_argument("--modes", default="solo,coop,assist")
    parser.add_argument("--player", default="strong", choices=("strong", "relaxed"))
    parser.add_argument("--helper-profile", default="helper", choices=("helper", "strong"))
    args = parser.parse_args(argv)
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]

    pygame.init()
    pygame.display.set_mode((320, 180))

    rows = []
    started = time.time()
    print("player %s, helper %s, hard, %g s per round" % (
        args.player, args.helper_profile, args.duration))
    print("%-6s %4s %6s %6s %6s %6s %s" % ("mode", "seed", "served", "failed",
                                           "stars", "helper", "policy"))
    print("-" * 52)
    for mode in modes:
        for seed in seeds:
            if mode == "solo":
                row = run(seed, player=args.player, duration=args.duration)
            else:
                row = run(seed, coop=True, player=args.player,
                          profile=args.helper_profile,
                          policy="assist" if mode == "assist" else "backlog",
                          duration=args.duration)
                row["mode"] = mode
            rows.append(row)
            print("%-6s %4d %6d %6d %6d %6d %s" % (
                row["mode"], row["seed"], row["served"], row["failed"],
                row["stars"], row["helper_serves"], row["policy"]))
    pygame.quit()

    print("-" * 52)
    print("elapsed %.1fs for %d rounds" % (time.time() - started, len(rows)))
    means = {}
    for mode in modes:
        picked = [r for r in rows if r["mode"] == mode]
        if not picked:
            continue
        stars = [r["stars"] for r in picked]
        means[mode] = statistics.mean(stars)
        print("%-6s stars=%s mean=%.1f helper_serves=%d bad=%d" % (
            mode, stars, means[mode],
            sum(r["helper_serves"] for r in picked),
            sum(1 for r in picked if r["problems"])))
    if "solo" in means and "coop" in means:
        print("solo mean %.1f (recorded %.1f) vs coop mean %.1f -> %+.1f" % (
            means["solo"], SOLO_BASELINE[args.player], means["coop"],
            means["coop"] - means["solo"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
