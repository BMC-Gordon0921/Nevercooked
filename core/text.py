"""Chinese-capable text rendering with a small surface cache."""
from __future__ import annotations

import os

import pygame

_REGULAR = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]
_BOLD = [r"C:\Windows\Fonts\msyhbd.ttc"] + _REGULAR
_fonts = {}
_cache = {}


def font(size, bold=False):
    key = (size, bold)
    if key in _fonts:
        return _fonts[key]
    chosen = None
    for candidate in (_BOLD if bold else _REGULAR):
        if os.path.exists(candidate):
            try:
                chosen = pygame.font.Font(candidate, size)
                break
            except (OSError, pygame.error):
                continue
    if chosen is None:
        chosen = pygame.font.SysFont("microsoftyahei", size, bold=bold)
    _fonts[key] = chosen
    return chosen


def render(value, size=14, color=(255, 255, 255), bold=False):
    """Cached text surface."""
    key = (value, size, color, bold)
    hit = _cache.get(key)
    if hit is None:
        hit = font(size, bold).render(value, True, color)
        _cache[key] = hit
    return hit


def shadow_text(surface, value, pos, size=14, color=(255, 255, 255), bold=False, anchor="topleft",
                shadow=(8, 10, 14)):
    """Text with a 1px drop shadow so it survives busy backgrounds."""
    surf = render(value, size, color, bold)
    rect = surf.get_rect(**{anchor: pos})
    dark = render(value, size, shadow, bold)
    surface.blit(dark, rect.move(1, 1))
    surface.blit(surf, rect)
    return rect
