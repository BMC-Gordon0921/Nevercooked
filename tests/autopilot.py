"""The two command-line switches and the takeover they enable.

  --superai  first tier (strong) plays the round
  --ai       second tier (relaxed) plays the round
  neither    the human plays

Checks the parser refuses both flags at once, that the app boots straight
into a round with a brain attached, that the brain is rebuilt for a new round
and that it actually serves something when left alone.

  python tests/autopilot.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

import main
from scenes.game import GameScene

STEP = 1.0 / 60.0
fails = []


def check(name, ok, note=""):
    print("%-46s %s %s" % (name, "ok" if ok else "FAIL", note))
    if not ok:
        fails.append(name)


def refused(argv):
    try:
        main.parse_args(argv)
    except SystemExit as exc:
        return exc.code
    return 0


def play(app, seconds):
    scene = app.scene
    for _ in range(int(seconds / STEP)):
        scene.update(STEP, app.autopilot_intent())
    return scene


def main_():
    pygame.init()
    pygame.display.set_mode((320, 180))

    check("no flag -> human plays", main.parse_args([]).superai is False
          and main.parse_args([]).ai is False)
    check("--superai -> strong", main.PROFILES["superai"] == "strong")
    check("--ai -> relaxed", main.PROFILES["ai"] == "relaxed")
    check("--superai --ai is refused", refused(["--superai", "--ai"]) == 2)
    check("--ai --superai is refused", refused(["--ai", "--superai"]) == 2)

    plain = main.App()
    check("plain app starts at the title", app_name(plain) == "TitleScene",
          app_name(plain))
    check("plain app hands out no intent", plain.autopilot_intent() is None)

    auto = main.App("strong")
    check("autopilot boots into a round", isinstance(auto.scene, GameScene),
          app_name(auto))
    check("autopilot round is hard", auto.scene.level == main.AUTOPILOT_LEVEL,
          auto.scene.level)
    first = auto.autopilot_intent()
    check("first frame returns an intent", first is not None)
    check("brain is cached for the round",
          auto.autopilot_intent() is not None and auto._brain is not None)

    scene = play(auto, 25.0)
    served = len(scene.world.orders.served)
    check("strong serves tickets unaided", served >= 1, "%d served in 25 s" % served)
    check("scene clock advanced", scene.elapsed > 20.0, "%.1f s" % scene.elapsed)

    old_brain = auto._brain
    auto.switch(GameScene(auto, "hard"))
    auto.autopilot_intent()
    check("a new round gets a new brain", auto._brain is not old_brain)

    soft = main.App("relaxed")
    check("second tier boots too", isinstance(soft.scene, GameScene))
    check("second tier reads the relaxed profile",
          soft._brain is None and soft.autopilot == "relaxed")

    print("-" * 60)
    print("AUTOPILOT: %s" % ("PASS" if not fails else "FAIL " + ",".join(fails)))
    return 0 if not fails else 1


def app_name(app):
    return type(app.scene).__name__


if __name__ == "__main__":
    sys.exit(main_())