"""Audio regression: every cue referenced by code exists, station cues fire once,
and a finished timer rings.  Run headless:
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/audio.py
"""
from __future__ import annotations

import os
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

pygame.init()
pygame.display.set_mode((320, 240))

from core import audio, config  # noqa: E402

PLAYED = []
_original_play = audio.play


def _spy(name, volume=0.7):
    PLAYED.append((name, volume))


audio.play = _spy


def referenced_names():
    names = set()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for folder in ("scenes", "game", "core"):
        for base, _dirs, files in os.walk(os.path.join(root, folder)):
            for name in files:
                if not name.endswith(".py"):
                    continue
                with open(os.path.join(base, name), "r", encoding="utf-8") as fh:
                    text = fh.read()
                names.update(re.findall(r'audio\.play(?:_bgm)?\(\s*"([a-z0-9_]+)"', text))
                # Cues chosen through a name tuple (the chop variants) never sit
                # next to audio.play(), so scan bare literals too.
                names.update(n for n in re.findall(r'"((?:sfx|bgm)_[a-z0-9_]+)"', text))
    return sorted(names)


def check_files():
    missing = []
    for name in referenced_names():
        if not os.path.exists(os.path.join(config.AUDIO_DIR, name + ".wav")):
            missing.append(name)
    print("cues:", ", ".join(referenced_names()))
    print("missing:", missing or "none")
    return not missing


def check_station_cues():
    from scenes.game import GameScene

    class App:
        def switch(self, scene):
            self.scene = scene

    scene = GameScene(App())
    ok = True
    for stype, expected in (("steamer", "sfx_steam"), ("wok", "sfx_sizzle"), ("oven", "sfx_oven")):
        station = next(s for s in scene.world.stations if s.stype == stype)
        station.phase = "cook"
        scene.target = station
        PLAYED.clear()
        scene._machine_sound("load")
        got = [n for n, _v in PLAYED]
        print("%-8s -> %s" % (stype, got or "nothing"))
        if got != [expected]:
            ok = False
    scene.target = None
    PLAYED.clear()
    scene._machine_sound("load")
    if PLAYED:
        print("no target must be silent, got", PLAYED)
        ok = False
    return ok


def check_ready_chime():
    from scenes.game import GameScene

    class App:
        def switch(self, scene):
            self.scene = scene

    scene = GameScene(App())
    station = scene.world.stations[0]
    station.phase = "cook"
    scene.phase_cache[id(station)] = "cook"
    PLAYED.clear()
    station.phase = "ready"
    scene._ready_chimes()
    first = list(PLAYED)
    scene._ready_chimes()
    second = list(PLAYED)[len(first):]
    print("ready chime:", first, "repeat:", second or "silent")
    names = [name for name, _volume in first]
    return names == ["sfx_ready"] and not second


def main():
    results = [("files", check_files()), ("station cues", check_station_cues()),
               ("ready chime", check_ready_chime())]
    for name, ok in results:
        print("%-14s %s" % (name, "PASS" if ok else "FAIL"))
    print("AUDIO:", "PASS" if all(ok for _n, ok in results) else "FAIL")
    return 0 if all(ok for _n, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
