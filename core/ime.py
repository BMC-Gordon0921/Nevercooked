"""Keep the OS input method away from the game keys.

Windows hands every window that accepts text to the IME, and then WASD can feed a
pinyin buffer instead of the game while Shift silently flips Chinese/English. SDL
only keeps IME composition alive while text input is started, so we stop it at
startup and again whenever the window regains focus.
"""
from __future__ import annotations

import os

import pygame


def preload():
    """Call before pygame.init(): stop SDL from raising the IME candidate window."""
    os.environ.setdefault("SDL_IME_SHOW_UI", "0")


def suppress():
    """Best effort; safe to call at any time, including every frame."""
    try:
        pygame.key.stop_text_input()
    except (AttributeError, pygame.error):
        pass


def is_focus(event):
    gained = getattr(pygame, "WINDOWFOCUSGAINED", None)
    return gained is not None and event.type == gained
