"""Redemption code: C on the title card, type it, Enter opens challenge mode."""
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
pygame.display.set_mode((320, 240))

from core import input as inputmod, profile
from game.systems import difficulty
from scenes.title import TitleScene


class FakeApp:
    def __init__(self):
        self.difficulty = "normal"
        self.running = True
        self.scenes = []

    def switch(self, scene):
        self.scenes.append(scene)


problems = []


def check(ok, label):
    print(("  ok   " if ok else "  FAIL ") + label)
    if not ok:
        problems.append(label)


def press(scene, **kw):
    intent = inputmod.Intent()
    for key, value in kw.items():
        setattr(intent, key, value)
    scene.update(1 / 60.0, intent)


def type_text(scene, text):
    for ch in text:
        press(scene, text=ch)


def fresh_profile():
    profile.PATH = os.path.join(tempfile.mkdtemp(), "profile.json")
    profile.save(profile._fresh())
    return profile.load()


# --- 1. input layer collects text, backspace and the C key -----------------
event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x, unicode="x")
intent = inputmod.read([event])
check(intent.text == "x", "KEYDOWN 'x' lands in intent.text")
event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode="\b")
intent = inputmod.read([event])
check(intent.backspace == 1 and intent.text == "", "backspace deletes, it is not text")
event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c, unicode="c")
intent = inputmod.read([event])
check(intent.code and intent.text == "c", "C opens the prompt and still types 'c'")
intent.clear_edges()
check(intent.text == "" and intent.backspace == 0 and not intent.code,
      "clear_edges resets the text fields")

# --- 2. codes live in difficulty.json, case and spaces do not matter -------
codes = difficulty.codes()
check(bool(codes), "difficulty.json ships at least one code")
check(difficulty.level_for_code(" xinggang ") == "hard", "lookup trims and ignores case")
check(difficulty.level_for_code("nope") is None, "unknown code returns None")

# --- 3. the whole title-card flow -----------------------------------------
data = fresh_profile()
check(not profile.is_unlocked("hard", data), "challenge mode starts locked")
app = FakeApp()
scene = TitleScene(app)
scene.data = data
press(scene, code=True)
check(scene.prompt_open, "C opens the code card")
type_text(scene, "xinggang")
check(scene.buffer == "xinggang", "typed buffer keeps the letters")
press(scene, backspace=2)
check(scene.buffer == "xingga", "backspace trims the buffer")
type_text(scene, "ng")
check(scene.buffer == "xinggang", "typing after a delete rebuilds the code")
press(scene, confirm=True)
check(not scene.prompt_open, "Enter closes the card")
check(profile.is_unlocked("hard", scene.data), "redeeming opens challenge mode")
check(scene.message_ok and "解锁" in scene.message, "the card reports the unlock")
check(scene.levels[scene.index] == "hard", "the picker jumps to the opened level")

press(scene, confirm=True)
check(bool(app.scenes), "Enter after redeeming starts a run")
if app.scenes:
    check(getattr(app.scenes[0], "level", None) == "hard", "that run is challenge mode")

# --- 4. wrong code, Esc, and redeeming twice -------------------------------
data = fresh_profile()
app = FakeApp()
scene = TitleScene(app)
scene.data = data
press(scene, code=True)
type_text(scene, "NOPE")
press(scene, confirm=True)
check(not profile.is_unlocked("hard", scene.data), "a wrong code unlocks nothing")
check((not scene.message_ok) and bool(scene.message), "a wrong code says so")
press(scene, code=True)
press(scene, text="X")
press(scene, menu=True)
check(not scene.prompt_open, "Esc leaves the card")

profile.unlock("hard", scene.data)
scene.data = profile.load()
press(scene, code=True)
type_text(scene, "NEVERCOOKED")
press(scene, confirm=True)
check(profile.is_unlocked("hard", scene.data), "a second code is harmless")
check(scene.message_ok, "redeeming what is already open is not an error")

# --- 5. Enter on a locked level explains itself ---------------------------
data = fresh_profile()
scene = TitleScene(FakeApp())
scene.data = data
scene.index = scene.levels.index("hard")
press(scene, confirm=True)
check(bool(scene.message) and not scene.message_ok,
      "Enter on a locked level explains instead of going quiet")

print("CODES: %s" % ("PASS" if not problems else "FAIL %d" % len(problems)))
sys.exit(1 if problems else 0)
