"""The cook. Foot collision box is 16x12 regardless of the 32x48 sprite."""
from __future__ import annotations

import pygame

from core import assets, config
from game.entities.base import Entity

FACING_DOWN = 0
FACING_UP = 1
FACING_SIDE = 2


class Actor(Entity):
    def __init__(self, foot):
        player = config.TUNING["player"]
        self.frames = assets.chef_placeholder((player["sprite_w"], player["sprite_h"]))
        super().__init__(foot, "chef_sheet", player["sprite_h"], layer_bias=1,
                         solid=False, color=(200, 208, 220),
                         sprite=self.frames[0])
        self.hand = None
        self.facing = (0, 1)
        self.facing_index = FACING_DOWN
        self.flip = False
        self.moving = False
        self.anim_t = 0.0
        self.sprint_t = 0.0
        self.sprint_cd = 0.0
        self.busy = 0.0
        self.busy_total = 0.0
        self.pending_action = None
        self.target = None
        self.target_age = 0.0
        self.walked = 0.0

    # -- facing ---------------------------------------------------------
    def face(self, dx, dy):
        if dx == 0 and dy == 0:
            return
        if abs(dx) > abs(dy):
            self.facing_index = FACING_SIDE
            self.flip = dx < 0
            self.facing = (1 if dx > 0 else -1, 0)
        else:
            self.facing_index = FACING_DOWN if dy > 0 else FACING_UP
            self.flip = False
            self.facing = (0, 1 if dy > 0 else -1)

    def facing_cell(self):
        """Centre of the tile this actor is looking at."""
        return (self.foot.centerx + self.facing[0] * config.TILE,
                self.foot.centery + self.facing[1] * config.TILE)

    # -- animation ------------------------------------------------------
    def current_frame(self):
        player = config.TUNING["player"]
        fps = player["walk_fps"] if self.moving else player["idle_fps"]
        step = int(self.anim_t * fps) % 4
        frame = self.frames[self.facing_index * 4 + step]
        if self.flip:
            frame = pygame.transform.flip(frame, True, False)
        return frame

    def update(self, dt):
        self.tick_alpha(dt)
        self.anim_t += dt
        self.sprite = self.current_frame()
        self.target_age += dt
        if self.sprint_cd > 0:
            self.sprint_cd = max(0.0, self.sprint_cd - dt)
        if self.busy > 0:
            self.busy = max(0.0, self.busy - dt)

    @property
    def busy_ratio(self):
        if self.busy_total <= 0:
            return 0.0
        return 1.0 - self.busy / self.busy_total
