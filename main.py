"""Entry point: one logical 1280x720 surface, integer-scaled to the desktop."""
from __future__ import annotations

import os
import sys

import pygame

from core import audio, config, ime
from core.input import Intent, read

ime.preload()

STEP = 1.0 / 60.0
MAX_STEPS = 5


class App:
    def __init__(self):
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
        self.scene = scene

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
                self.scene.update(STEP, pending)
                pending.clear_edges()
                pending = Intent()
                accumulator -= STEP
                steps += 1
            if steps:
                self.scene.draw(self.logical)
                self.present()
        pygame.quit()


def main(argv=None):
    app = App()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
