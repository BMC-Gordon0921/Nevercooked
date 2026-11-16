"""World->screen: one integer zoom, one clamped follow. No smoothing needed."""
from __future__ import annotations

import pygame

from core import config


class Camera:
    """Every draw call asks the camera where a world point lands on screen."""

    def __init__(self, zoom=2, origin=(0, config.GAME_TOP),
                 view_w=config.SCREEN_W, view_h=config.GAME_H):
        self.zoom = int(zoom)
        self.ox, self.oy = origin
        self.view_w = int(view_w)
        self.view_h = int(view_h)
        self.x = 0
        self.y = 0
        self.bounds = pygame.Rect(0, 0, self.world_w, self.world_h)
        self._scaled = {}

    # -- geometry -------------------------------------------------------
    @property
    def world_w(self):
        return self.view_w // self.zoom

    @property
    def world_h(self):
        return self.view_h // self.zoom

    def set_bounds(self, rect):
        self.bounds = pygame.Rect(rect)
        self.center_on((self.bounds.centerx, self.bounds.centery))

    def center_on(self, point):
        """Keep the view inside the bounds; a small world just sits in the middle."""
        b = self.bounds
        vw, vh = self.world_w, self.world_h
        x = int(point[0]) - vw // 2
        y = int(point[1]) - vh // 2
        if b.w <= vw:
            x = b.x + (b.w - vw) // 2
        else:
            x = max(b.x, min(x, b.right - vw))
        if b.h <= vh:
            y = b.y + (b.h - vh) // 2
        else:
            y = max(b.y, min(y, b.bottom - vh))
        self.x, self.y = x, y

    # -- mapping --------------------------------------------------------
    def sx(self, world_x):
        return self.ox + int((world_x - self.x) * self.zoom)

    def sy(self, world_y):
        return self.oy + int((world_y - self.y) * self.zoom)

    def rect(self, world_rect):
        z = self.zoom
        return pygame.Rect(self.sx(world_rect.x), self.sy(world_rect.y),
                           world_rect.w * z, world_rect.h * z)

    def sprite(self, surface):
        """Nearest-neighbour upscale, cached: pixel art stays crisp at 2x."""
        key = id(surface)
        hit = self._scaled.get(key)
        if hit is not None and hit[0] is surface:
            return hit[1]
        z = self.zoom
        big = pygame.transform.scale(
            surface, (surface.get_width() * z, surface.get_height() * z))
        self._scaled[key] = (surface, big)
        return big
