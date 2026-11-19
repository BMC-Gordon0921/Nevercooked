"""Entry point: one logical 1280x720 surface, integer-scaled to the desktop.

Two flags hand the keyboard to the chef brain in game/systems/ai.py, so the
AI tiers can be watched (or recorded) exactly as a player would see them:

  python main.py             you play, from the title screen
  python main.py --superai   first tier (strong) takes over, round starts at once
  python main.py --ai        second tier (relaxed) takes over, round starts at once

The two are mutually exclusive; anything that is not a live round (title,
results, settings) still belongs to the human, so Esc out and keep playing.
"""
from __future__ import annotations

import argparse
import os
import sys

import pygame

from core import audio, config, ime, profile
from core.input import Intent, read

ime.preload()

STEP = 1.0 / 60.0
MAX_STEPS = 5

#: Both flags start the same round, so the two tiers are compared on one
#: difficulty instead of two.  Hard is the mode the benchmark measures.
AUTOPILOT_LEVEL = "hard"

PROFILES = {"superai": "strong", "ai": "relaxed"}


class App:
    def __init__(self, autopilot=None, coop=None, helper=None, helper_policy=None):
        stored = profile.settings()
        # CLI beats the persisted setting; --helper off wins over everything.
        if helper == "off":
            self.coop = False
        elif helper:
            self.coop = True
        elif coop is not None:
            self.coop = bool(coop)
        else:
            self.coop = bool(stored.get("coop", False))
        self.helper_profile = helper if helper in ("helper", "strong") else stored.get("helper_profile", "helper")
        self.helper_policy = helper_policy or stored.get("helper_policy", "backlog")
        pygame.init()
        audio.init()
        pygame.display.set_caption("欢闹厨房！  Nevercooked!")
        self.scale = self._pick_scale()
        size = (config.SCREEN_W * self.scale, config.SCREEN_H * self.scale)
        flags = 0
        self.screen = pygame.display.set_mode(size, flags)
        ime.suppress()
        self.logical = pygame.Surface((config.SCREEN_W, config.SCREEN_H)).convert()
        self.running = True
        self.autopilot = autopilot
        self._brain = None
        self._brain_scene = None
        if autopilot:
            from scenes.game import GameScene
            self.difficulty = AUTOPILOT_LEVEL
            self.scene = GameScene(self, AUTOPILOT_LEVEL)
            print("[AI] %s profile is playing this round (%s)" % (autopilot, AUTOPILOT_LEVEL))
        else:
            from scenes.title import TitleScene
            self.scene = TitleScene(self)

    @staticmethod
    def _pick_scale():
        try:
            info = pygame.display.Info()
            wide = info.current_w // config.SCREEN_W
            high = info.current_h // config.SCREEN_H
            return max(1, min(wide, high))
        except pygame.error:
            return 1

    def switch(self, scene):
        from scenes.title import TitleScene
        if isinstance(scene, TitleScene):
            self.autopilot = None
            self._brain = None
            self._brain_scene = None
        self.scene = scene

    def step(self, intent):
        # Menu controls remain human-owned, including while the AI is paused.
        if (getattr(self.scene, "paused", False) or intent.menu or intent.settings):
            chosen = intent
        else:
            auto = self.autopilot_intent()
            chosen = intent if auto is None else auto
        self.scene.update(STEP, chosen)

    def autopilot_intent(self):
        """The brain's Intent for this step, or None while a human is playing.

        A fresh brain is built for every round, so a restart from the results
        screen does not inherit the previous round's missions.
        """
        if not self.autopilot:
            return None
        scene = self.scene
        if getattr(scene, "world", None) is None:
            return None
        if self._brain_scene is not scene:
            from game.systems.ai import Brain
            self._brain = Brain(self.autopilot)
            self._brain_scene = scene
        return self._brain.think(scene)

    def present(self):
        if self.scale == 1:
            self.screen.blit(self.logical, (0, 0))
        else:
            pygame.transform.scale(self.logical, self.screen.get_size(), self.screen)
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        accumulator = 0.0
        limit = int(os.environ.get("MW_FRAMES", "0"))
        frames = 0
        while self.running:
            if limit:
                frames += 1
                if frames > limit:
                    break
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif ime.is_focus(event):
                    ime.suppress()
            intent = read(events)
            frame_dt = min(clock.tick(60) / 1000.0, 0.2)
            accumulator += frame_dt
            steps = 0
            pending = intent
            while accumulator >= STEP and steps < MAX_STEPS:
                self.step(pending)
                pending.clear_edges()
                accumulator -= STEP
                steps += 1
            if steps:
                self.scene.draw(self.logical)
                self.present()
        pygame.quit()


def parse_args(argv=None):
    """--superai and --ai are alternatives: one chef, one brain."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="欢闹厨房！ Nevercooked! 不带参数时进标题界面自己玩。")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--superai", action="store_true",
                       help="第一档 AI（strong）接管玩家行动，直接开局")
    group.add_argument("--ai", action="store_true",
                       help="第二档 AI（relaxed）接管玩家行动，直接开局")
    parser.add_argument("--coop", action="store_true",
                        help="开局就带 AI 帮厨（灶罐），由设置里的档位与倾向驱动")
    parser.add_argument("--helper", choices=("off", "helper", "strong"), default=None,
                        help="帮厨熟练度：off 关闭双人，helper 学徒，strong 熟手")
    parser.add_argument("--helper-policy", choices=("backlog", "assist"), default=None,
                        help="帮厨倾向：backlog 补单（清积压），assist 辅助（只接急单）")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    autopilot = None
    if args.superai:
        autopilot = PROFILES["superai"]
    elif args.ai:
        autopilot = PROFILES["ai"]
    app = App(autopilot, coop=(args.coop or None), helper=args.helper,
              helper_policy=args.helper_policy)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
