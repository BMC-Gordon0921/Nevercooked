"""Common entity contract for the depth-sorted world."""
from __future__ import annotations

import pygame

from core import assets


class Entity:
    """Anything with a floor footprint that participates in L2 depth sorting.

    The sprite is anchored so its bottom-centre sits on the footprint's
    bottom-centre, which keeps the 3/4 stacking readable for any height.
    """

    def __init__(self, foot, sprite_key, height, layer_bias=0, solid=None,
                 color=(110, 120, 140), label=None, sprite=None):
        self.foot = pygame.Rect(foot)
        self.height = height
        self.layer_bias = layer_bias
        self.solid = (height >= 24) if solid is None else solid
        if sprite is None:
            sprite = assets.image(sprite_key, (self.foot.w, height), color, label)
        self.sprite = sprite
        self.alpha = 255.0
        self.alpha_target = 255.0
        self.alive = True

    @property
    def sort_key(self):
        return self.foot.bottom * 1000 + self.layer_bias

    def sprite_rect(self):
        rect = self.sprite.get_rect()
        rect.midbottom = (self.foot.centerx, self.foot.bottom)
        return rect

    def tick_alpha(self, dt, seconds=0.12):
        if abs(self.alpha - self.alpha_target) < 0.5:
            self.alpha = float(self.alpha_target)
            return
        step = 255.0 * dt / max(0.016, seconds)
        if self.alpha < self.alpha_target:
            self.alpha = min(self.alpha_target, self.alpha + step)
        else:
            self.alpha = max(self.alpha_target, self.alpha - step)

    def update(self, dt):
        self.tick_alpha(dt)
