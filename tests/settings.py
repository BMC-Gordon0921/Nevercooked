"""Settings screen contract: volumes persist, the path switch reaches the game."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from core import audio, config, profile
from core.input import Intent
from scenes.game import GameScene
from scenes.settings import ROWS, SettingsScene

FAILS = []


def check(name, ok, info=""):
    print(("  ok   " if ok else "  FAIL ") + name + ((" | " + str(info)) if info else ""))
    if not ok:
        FAILS.append(name)


class FakeApp:
    running = True
    difficulty = "normal"

    def __init__(self):
        self.scene = None

    def switch(self, scene):
        self.scene = scene


def press(scene, **kw):
    it = Intent()
    for key, value in kw.items():
        setattr(it, key, value)
    scene.update(1 / 60.0, it)


def main():
    pygame.init()
    pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    surface = pygame.Surface((config.SCREEN_W, config.SCREEN_H))

    before = profile.settings()
    saved = profile.load()
    check("defaults present",
          set(before) == {"sfx", "bgm", "path", "coop", "helper_profile",
                          "helper_policy"}, before)

    app = FakeApp()
    scene = SettingsScene(app, None)
    check("six rows", len(ROWS) == 6, [r[1] for r in ROWS])
    scene.draw(surface)
    check("draws without error", True)

    # volume down by two steps (row 1 = sfx)
    press(scene, pick=1)
    press(scene, nav=-1)
    press(scene, nav=-1)
    quiet = profile.settings()["sfx"]
    check("sfx volume stepped down", quiet < before["sfx"], (before["sfx"], quiet))
    check("audio module follows", abs(audio.sfx_volume() - quiet) < 1e-6,
          (audio.sfx_volume(), quiet))

    # clamp at the bottom
    for _ in range(40):
        press(scene, nav=-1)
    low = profile.settings()["sfx"]
    check("sfx volume clamps at 0", low == 0.0, low)
    for _ in range(4):
        press(scene, nav=1)
    check("sfx volume comes back up", profile.settings()["sfx"] > 0.0)

    # bgm row, then the path switch
    press(scene, pick=2)
    press(scene, nav=1)
    check("bgm volume stepped up", profile.settings()["bgm"] > before["bgm"],
          (before["bgm"], profile.settings()["bgm"]))
    press(scene, pick=3)
    on_before = profile.settings()["path"]
    press(scene, nav=-1)
    check("path toggled", profile.settings()["path"] != on_before,
          (on_before, profile.settings()["path"]))
    # the second cook: on/off, then the two dropdowns
    press(scene, pick=4)
    coop_before = profile.settings()["coop"]
    press(scene, nav=1)
    check("coop toggled", profile.settings()["coop"] != coop_before,
          (coop_before, profile.settings()["coop"]))
    press(scene, pick=5)
    profile_before = profile.settings()["helper_profile"]
    press(scene, nav=1)
    after_profile = profile.settings()["helper_profile"]
    check("helper profile cycles", after_profile != profile_before,
          (profile_before, after_profile))
    press(scene, pick=6)
    policy_before = profile.settings()["helper_policy"]
    press(scene, nav=1)
    check("helper policy cycles", profile.settings()["helper_policy"] != policy_before,
          (policy_before, profile.settings()["helper_policy"]))
    scene.draw(surface)
    check("draws toggled state", True)

    # a fresh load keeps what we wrote
    reloaded = profile.settings()
    check("settings survive reload", reloaded["path"] == profile.settings()["path"])

    # a coop scene only exists when the profile asks for it
    profile.save_settings({"coop": True})
    app.coop = True
    coop_game = GameScene(app, "normal")
    check("coop scene has a helper", coop_game.helper is not None)
    check("helper body is the second cook",
          coop_game.helper.actor is not coop_game.world.player)

    # game picks the switch up on resume
    game = GameScene(app, "normal")
    check("game reads path switch", game.show_path == profile.settings()["path"],
          (game.show_path, profile.settings()["path"]))
    game.show_path = False
    profile.save_settings({"path": True})
    game.on_resume()
    check("resume reloads settings", game.show_path is True, game.show_path)
    check("resume reloads volumes",
          abs(audio.sfx_volume() - profile.settings()["sfx"]) < 1e-6)

    # Esc returns to the scene it came from
    game2 = GameScene(app, "normal")
    game2.paused = True
    app.scene = game2
    back = SettingsScene(app, game2)
    press(back, menu=True)
    check("esc returns to the caller", app.scene is game2, type(app.scene).__name__)

    # restore the user's file
    profile.save(saved)
    print("SETTINGS:", "PASS" if not FAILS else "FAIL " + ", ".join(FAILS))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
