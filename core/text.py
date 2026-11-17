"""Chinese-capable text rendering: hard pixel glyphs first, TTF only as a net.

Every scene draws through this module, so it is the single switch between the
bitmap pipeline and the old rasteriser:

  * core.pixelfont draws the baked 12px atlas at whole-number scales, so glyph
    edges are always alpha 0 or 255 - no antialiasing, ever.
  * Characters the atlas has no glyph for (rare CJK, some arrows) fall back to
    the system TTF with antialiasing disabled, so they still appear instead of
    turning into blank boxes.

Layout sizes are snapped by pixelfont.scale_for(): <=19 -> 12px, 20..33 ->
24px, 34..59 -> 36px, 60..79 -> 60px, 80+ -> 84px.

    font(size, bold=False)   -> pygame.font.Font (TTF fallback path)
    render(value, size=14, color=(255, 255, 255), bold=False) -> cached Surface
    shadow_text(surface, value, pos, size=14, color=..., bold=False,
                anchor="topleft", shadow=(8, 10, 14)) -> Rect
"""
from __future__ import annotations

import os

import pygame

from core import pixelfont

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


def _draw(value, size, color, bold):
    """Pixel path when the atlas covers every char, TTF (no AA) otherwise."""
    if value and pixelfont.ready() and pixelfont.covers(value):
        try:
            return pixelfont.render(value, pixelfont.scale_for(size), color, bold)
        except (pygame.error, ValueError, KeyError, TypeError):
            pass
    return font(size, bold).render(value, False, color)


def render(value, size=14, color=(255, 255, 255), bold=False):
    """Cached text surface, pixel-perfect when the atlas can draw it."""
    key = (value, size, color, bold)
    hit = _cache.get(key)
    if hit is None:
        hit = _draw(value, size, color, bold)
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


def scale_for(size):
    """Integer atlas scale the given layout size renders at."""
    return pixelfont.scale_for(size)


def clear_cache():
    """Drop cached surfaces and atlas glyphs (tests)."""
    _cache.clear()
    pixelfont.clear_cache()
