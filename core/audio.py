"""Audio playback that degrades silently when a file or the mixer is missing."""
from __future__ import annotations

import os

import pygame

from core import config

_sounds = {}
_enabled = True
_current_bgm = None


def enabled():
    return _enabled


def init():
    global _enabled
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(16)
    except pygame.error:
        _enabled = False


def sound(name, volume=0.7):
    """Fetch (and lazily load) a sound effect by file stem."""
    if not _enabled:
        return None
    if name in _sounds:
        return _sounds[name]
    path = os.path.join(config.AUDIO_DIR, name + ".wav")
    loaded = None
    if os.path.exists(path):
        try:
            loaded = pygame.mixer.Sound(path)
            loaded.set_volume(volume)
        except pygame.error:
            loaded = None
    _sounds[name] = loaded
    return loaded


def play(name, volume=0.7):
    snd = sound(name, volume)
    if snd is not None:
        snd.set_volume(volume)
        snd.play()


def play_bgm(name, volume=0.35):
    global _current_bgm
    if not _enabled or _current_bgm == name:
        return
    path = os.path.join(config.AUDIO_DIR, name + ".wav")
    if not os.path.exists(path):
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
        _current_bgm = name
    except pygame.error:
        pass


def stop_bgm():
    global _current_bgm
    _current_bgm = None
    if _enabled:
        pygame.mixer.music.stop()
