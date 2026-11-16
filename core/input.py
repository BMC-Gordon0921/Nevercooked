"""Translate pygame events and key state into one intent struct."""
from __future__ import annotations

import pygame

_RIGHT = (pygame.K_d, pygame.K_RIGHT)
_LEFT = (pygame.K_a, pygame.K_LEFT)
_DOWN = (pygame.K_s, pygame.K_DOWN)
_UP = (pygame.K_w, pygame.K_UP)


class Intent:
    __slots__ = ("mx", "my", "sprint", "interact", "throw", "menu", "confirm")

    def __init__(self):
        self.mx = 0
        self.my = 0
        self.sprint = False
        self.interact = False
        self.throw = False
        self.menu = False
        self.confirm = False

    def clear_edges(self):
        self.interact = False
        self.throw = False
        self.confirm = False


def read(events):
    """Build an intent from this frame's events plus held-key state."""
    intent = Intent()
    keys = pygame.key.get_pressed()
    mx = 0
    my = 0
    if any(keys[k] for k in _RIGHT):
        mx += 1
    if any(keys[k] for k in _LEFT):
        mx -= 1
    if any(keys[k] for k in _DOWN):
        my += 1
    if any(keys[k] for k in _UP):
        my -= 1
    intent.mx = mx
    intent.my = my
    # Shift for keyboards, right mouse button for mice. Space stays free.
    mouse = pygame.mouse.get_pressed(3)
    intent.sprint = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or mouse[2])

    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                intent.interact = True
            elif event.key == pygame.K_q:
                intent.throw = True
            elif event.key == pygame.K_ESCAPE:
                intent.menu = True
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                intent.confirm = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                intent.interact = True
    return intent
