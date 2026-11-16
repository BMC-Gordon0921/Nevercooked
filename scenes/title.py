"""Title card: bright canteen light, one key to start."""
from __future__ import annotations

import math

import pygame

from core import assets, audio, config, text as textmod

COL_IVORY = config.color("ivory")
COL_SAND = config.color("sand")
COL_GLASS = config.color("glass")
COL_TEAL = config.color("teal")
COL_INK = config.color("ink")
COL_STEEL = config.color("steel")
COL_FLAME = config.color("flame_deep")
COL_AMBER = config.color("amber")
COL_CREAM = config.color("cream")
SHADOW = (66, 52, 38)


class TitleScene:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        audio.play_bgm("bgm_canteen_loop", 0.20)

    def update(self, dt, intent):
        self.t += dt
        if intent.confirm:
            from scenes.game import GameScene
            self.app.switch(GameScene(self.app))
        elif intent.menu:
            self.app.running = False

    def _sky(self, surface):
        top = COL_GLASS
        bottom = COL_IVORY
        bands = 32
        step = config.SCREEN_H // bands
        for index in range(bands):
            f = index / (bands - 1)
            col = tuple(int(top[c] + (bottom[c] - top[c]) * f) for c in range(3))
            pygame.draw.rect(surface, col, (0, index * step, config.SCREEN_W, step + 1))

    def _floor_strip(self, surface):
        y_top = config.SCREEN_H - 132
        pygame.draw.rect(surface, COL_SAND, (0, y_top, config.SCREEN_W, 132))
        tile = assets.image("floor_a", (config.TILE, config.TILE))
        for col in range(0, config.SCREEN_W // config.TILE + 1):
            for row in range(2):
                surface.blit(tile, (col * config.TILE, y_top + 4 + row * config.TILE))
        veil = pygame.Surface((config.SCREEN_W, 132), pygame.SRCALPHA)
        veil.fill((247, 242, 230, 120))
        surface.blit(veil, (0, y_top))
        pygame.draw.line(surface, config.color("clay"), (0, y_top), (config.SCREEN_W, y_top), 2)

    def draw(self, surface):
        self._sky(surface)
        # one warm lamp glow behind the wordmark
        glow = pygame.Surface((560, 260), pygame.SRCALPHA)
        for radius in range(120, 8, -12):
            alpha = int(9 * (1 - radius / 130.0) * 4)
            pygame.draw.circle(glow, (255, 214, 120, max(0, alpha)), (280, 130), radius)
        surface.blit(glow, (config.SCREEN_W // 2 - 280, 96))
        self._floor_strip(surface)

        cx = config.SCREEN_W // 2
        textmod.shadow_text(surface, "乱灶", (cx - 150, 218), size=84, color=COL_FLAME,
                            bold=True, anchor="center", shadow=SHADOW)
        textmod.shadow_text(surface, "星港食堂", (cx + 132, 218), size=84, color=COL_TEAL,
                            bold=True, anchor="center", shadow=SHADOW)
        textmod.shadow_text(surface, "MESSY WOK  ·  STARPORT CANTEEN", (cx, 282),
                            size=18, color=COL_STEEL, anchor="center", shadow=(255, 255, 255))
        textmod.shadow_text(surface, "碗底港 · 第七码头  ·  三分钟一局", (cx, 318),
                            size=17, color=COL_INK, anchor="center", shadow=(255, 255, 255))

        pulse = int(170 + 70 * math.sin(self.t * 3.0))
        pygame.draw.rect(surface, COL_CREAM, (cx - 150, 396, 300, 62), border_radius=10)
        pygame.draw.rect(surface, config.color("clay"), (cx - 150, 396, 300, 62), 2, border_radius=10)
        textmod.shadow_text(surface, "按 Enter 开始", (cx, 427), size=27,
                            color=(min(240, pulse + 40), min(150, pulse), 40), bold=True,
                            anchor="center", shadow=(255, 255, 255))
        textmod.shadow_text(surface, "WASD 移动   右键/Shift 冲刺   F 交互   Q 抛出   Esc 退出",
                            (cx, config.SCREEN_H - 44), size=15, color=COL_INK, anchor="center",
                            shadow=COL_SAND)
