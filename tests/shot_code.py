"""Screenshot the redemption-card state of the title screen."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from core import input as inputmod
from scenes.title import TitleScene


class FakeApp:
    difficulty = "normal"
    running = True

    def switch(self, scene):
        pass


scene = TitleScene(FakeApp())
surface = pygame.Surface((1280, 720))


def press(**kw):
    intent = inputmod.Intent()
    for key, value in kw.items():
        setattr(intent, key, value)
    scene.update(1 / 60.0, intent)


press(code=True)
for ch in "XINGG":
    press(text=ch)
scene.draw(surface)
pygame.image.save(surface, "tests/shot_v2_code.png")
print("saved tests/shot_v2_code.png")
