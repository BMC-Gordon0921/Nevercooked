"""Audio playback that degrades silently when a file or the mixer is missing.

Two master volumes sit on top of the per-cue volumes so the settings screen can
move the whole mix: `sfx` scales every one-shot, `bgm` scales the music.  Both
are plain multipliers -- a cue asking for 0.7 still means "0.7 of the sfx bus".
"""
from __future__ import annotations

import os

import pygame

from core import config

_sounds = {}
_enabled = True
_current_bgm = None
_bgm_base = 0.35
_sfx_volume = 1.0
_bgm_volume = 1.0


def _clamp(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if value < 0.0 else 1.0 if value > 1.0 else value


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


def sfx_volume():
    return _sfx_volume


def bgm_volume():
    return _bgm_volume


def set_sfx_volume(value):
    global _sfx_volume
    _sfx_volume = _clamp(value)
    return _sfx_volume


def set_bgm_volume(value):
    """Scale the music bus; a playing track follows immediately."""
    global _bgm_volume
    _bgm_volume = _clamp(value)
    if _enabled and _current_bgm:
        try:
            pygame.mixer.music.set_volume(_bgm_base * _bgm_volume)
        except pygame.error:
            pass
    return _bgm_volume


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
            loaded.set_volume(_clamp(volume))
        except pygame.error:
            loaded = None
    _sounds[name] = loaded
    return loaded


def play(name, volume=0.7):
    snd = sound(name, volume)
    if snd is not None:
        snd.set_volume(_clamp(volume) * _sfx_volume)
        snd.play()


def play_bgm(name, volume=0.35):
    global _current_bgm, _bgm_base
    if not _enabled or _current_bgm == name:
        return
    path = os.path.join(config.AUDIO_DIR, name + ".wav")
    if not os.path.exists(path):
        return
    try:
        _bgm_base = _clamp(volume)
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(_bgm_base * _bgm_volume)
        pygame.mixer.music.play(-1)
        _current_bgm = name
    except pygame.error:
        pass


def stop_bgm():
    global _current_bgm
    _current_bgm = None
    if _enabled:
        pygame.mixer.music.stop()
