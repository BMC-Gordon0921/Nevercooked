"""Input ownership, catch-up movement, and damaged-profile regressions."""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import main
from core import profile
from core.input import Intent
from scenes.game import GameScene
from scenes.settings import SettingsScene
from scenes.title import TitleScene


class Regressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = patch.object(profile, "PATH", os.path.join(self.temp.name, "profile.json"))
        self.path.start()

    def tearDown(self):
        self.path.stop()
        self.temp.cleanup()
        pygame.quit()

    def test_ai_menus_and_return_to_human(self):
        app = main.App("strong")
        game = app.scene
        key = Intent()
        key.menu = True
        app.step(key)
        self.assertTrue(game.paused)
        elapsed = game.elapsed
        app.step(Intent())
        self.assertEqual(game.elapsed, elapsed)
        app.step(key)
        self.assertFalse(game.paused)
        key = Intent()
        key.settings = True
        app.step(key)
        self.assertIsInstance(app.scene, SettingsScene)
        key = Intent()
        key.menu = True
        app.step(key)
        self.assertIs(app.scene, game)
        self.assertTrue(game.paused)
        key = Intent()
        key.confirm = True
        app.step(key)
        self.assertIsInstance(app.scene, TitleScene)
        self.assertIsNone(app.autopilot)
        app.switch(GameScene(app, "normal"))
        self.assertIsNone(app.autopilot_intent())

    def test_catchup_retains_held_input_but_not_edges(self):
        app = main.App()
        key = Intent()
        key.mx = 1
        key.sprint = key.interact = key.interact_held = True
        seen = []
        def capture(dt, intent):
            seen.append((intent.mx, intent.sprint, intent.interact_held, intent.interact))
        clock = unittest.mock.Mock()
        clock.tick.return_value = 50
        with patch.object(app.scene, "update", side_effect=capture), \
             patch.object(main, "read", return_value=key), \
             patch.object(pygame.time, "Clock", return_value=clock), \
             patch.dict(os.environ, {"MW_FRAMES": "1"}):
            app.run()
        self.assertGreaterEqual(len(seen), 2)
        self.assertEqual(seen[0], (1, True, True, True))
        self.assertTrue(all(row == (1, True, True, False) for row in seen[1:]))

    def test_damaged_profile_preserves_valid_fields(self):
        for runs in ("broken", {}, [], float("inf"), -5):
            with open(profile.PATH, "w", encoding="utf-8") as out:
                json.dump({"runs": runs, "best": {"normal": 450, "bad": float("nan")},
                           "unlocked": ["hard", "bogus", "hard"],
                           "settings": {"sfx": float("nan"), "bgm": .4}}, out)
            data = profile.load()
            self.assertEqual(data["runs"], 0)
            self.assertEqual(data["best"], {"normal": 450})
            self.assertEqual(data["unlocked"], ["easy", "normal", "hard"])
            self.assertEqual(data["settings"]["sfx"], .8)
            self.assertEqual(data["settings"]["bgm"], .4)


if __name__ == "__main__":
    unittest.main()
