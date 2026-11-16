"""Sprite loading with generated placeholder fallbacks.

Real art lives in assets/art/<key>.png. Until a PNG exists the loader builds a
greybox stand-in that already respects the 3/4 silhouette contract, so gameplay
and depth sorting can be tuned before any pixel art lands.
"""
from __future__ import annotations

import os

import pygame

from core import config

_cache = {}
_sheets = {}


def _shade(rgb, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in rgb)


def placeholder(w, h, color, label=None):
    """Cheap 3/4 box: bright top face, base front face, dark rim."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    top_h = max(6, int(h * 0.2))
    pygame.draw.rect(surf, _shade(color, 0.8), pygame.Rect(0, top_h, w, h - top_h))
    pygame.draw.rect(surf, _shade(color, 1.15), pygame.Rect(0, 0, w, top_h + 4))
    dark_h = max(3, h // 8)
    pygame.draw.rect(surf, _shade(color, 0.45), pygame.Rect(0, h - dark_h, w, dark_h))
    pygame.draw.rect(surf, (11, 14, 20), surf.get_rect(), 1)
    if label:
        from core import text as textmod
        size = max(9, min(13, w // 2))
        glyph = textmod.render(label[:2], size, (20, 24, 32))
        surf.blit(glyph, glyph.get_rect(center=(w // 2, int(h * 0.62))))
    return surf


def image(key, size=(32, 32), color=(110, 120, 140), label=None):
    """Load assets/art/<key>.png or synthesise a placeholder of the same size."""
    hit = _cache.get(key)
    if hit is not None:
        return hit
    path = os.path.join(config.ART_DIR, key + ".png")
    if os.path.exists(path):
        surf = pygame.image.load(path)
        try:
            surf = surf.convert_alpha()
        except pygame.error:
            pass
    else:
        surf = placeholder(size[0], size[1], color, label)
    _cache[key] = surf
    return surf


def sheet(key, frame_w, frame_h):
    """Load a horizontal sprite sheet and return its frames."""
    cache_key = (key, frame_w)
    if cache_key in _sheets:
        return _sheets[cache_key]
    surf = image(key, (frame_w, frame_h))
    count = max(1, surf.get_width() // frame_w)
    frames = []
    for index in range(count):
        frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
        frame.blit(surf, (0, 0), pygame.Rect(index * frame_w, 0, frame_w, frame_h))
        frames.append(frame)
    _sheets[cache_key] = frames
    return frames


def chef_placeholder(size=(32, 48)):
    """Stand-in chef that shows facing and stride, used before art exists."""
    key = "chef_placeholder_%dx%d" % size
    hit = _cache.get(key)
    if hit is not None:
        return hit
    frames = []
    w, h = size
    for facing, accent in ((0, (56, 225, 255)), (1, (255, 194, 75)), (2, (255, 63, 164))):
        for step in range(4):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            bob = (0, 1, 0, -1)[step]
            body = pygame.Rect(w // 2 - 8, 14 + bob, 16, 22)
            pygame.draw.rect(surf, (200, 208, 220), body)
            pygame.draw.rect(surf, (46, 54, 70), body, 1)
            head = pygame.Rect(w // 2 - 6, 2 + bob, 12, 12)
            pygame.draw.rect(surf, (244, 230, 200), head)
            pygame.draw.rect(surf, (46, 54, 70), head, 1)
            pygame.draw.rect(surf, accent, pygame.Rect(head.x + 3, head.y + 5, 2, 3))
            pygame.draw.rect(surf, accent, pygame.Rect(head.right - 5, head.y + 5, 2, 3))
            leg_y = 36 + bob
            pygame.draw.rect(surf, (28, 34, 48), pygame.Rect(w // 2 - 6, leg_y, 5, 10 if step % 2 else 8))
            pygame.draw.rect(surf, (28, 34, 48), pygame.Rect(w // 2 + 1, leg_y, 5, 8 if step % 2 else 10))
            if facing == 1:
                pygame.draw.rect(surf, (28, 34, 48), pygame.Rect(w // 2 - 6, 6 + bob, 12, 7))
            frames.append(surf)
    _cache[key] = frames
    return frames
