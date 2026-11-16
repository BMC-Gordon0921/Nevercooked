"""Closing till: what you earned, what you wasted, what you carry out."""
from __future__ import annotations

import pygame

from core import config, profile, text as textmod
from game.systems import difficulty

COL_IVORY = config.color("ivory")
COL_CREAM = config.color("cream")
COL_SAND = config.color("sand")
COL_INK = config.color("ink")
COL_SLATE = config.color("slate")
COL_STEEL = config.color("steel")
COL_AMBER = config.color("amber")
COL_GOLD = (188, 124, 16)
COL_FLAME = config.color("flame_deep")
COL_TEAL = config.color("teal")
COL_LIME = config.color("leaf")
COL_TOMATO = config.color("tomato")
COL_CLAY = config.color("clay")
SHADOW = (255, 255, 255)


def rank_of(stars):
    if stars >= 420:
        return "S  灶神下凡", COL_GOLD
    if stars >= 260:
        return "A  忙而不乱", COL_LIME
    if stars >= 130:
        return "B  勉强开张", COL_TEAL
    return "C  兵荒马乱", COL_TOMATO


class ResultsScene:
    def __init__(self, app, score, level=None):
        self.app = app
        self.score = score
        self.level = level or getattr(app, "difficulty", difficulty.DEFAULT)
        self.info = difficulty.data(self.level)
        self.t = 0.0
        stars = score.final_stars()
        self.stars = stars
        self.coins = score.coins()
        self.data, self.opened = profile.record(self.level, stars)

    def update(self, dt, intent):
        self.t += dt
        if self.t < 0.4:
            return
        if intent.confirm:
            from scenes.game import GameScene
            self.app.switch(GameScene(self.app, self.level))
        elif intent.menu:
            from scenes.title import TitleScene
            self.app.switch(TitleScene(self.app))

    def draw(self, surface):
        surface.fill(COL_IVORY)
        cx = config.SCREEN_W // 2
        card = pygame.Rect(0, 0, 620, 560)
        card.center = (cx, config.SCREEN_H // 2 + 6)
        pygame.draw.rect(surface, (206, 190, 164), card.move(0, 6), border_radius=14)
        pygame.draw.rect(surface, COL_CREAM, card, border_radius=14)
        pygame.draw.rect(surface, COL_CLAY, card, 2, border_radius=14)

        top = card.top + 34
        textmod.shadow_text(surface, "收摊结算", (cx, top), size=40, color=COL_INK,
                            bold=True, anchor="center", shadow=SHADOW)
        rank, color = rank_of(self.stars)
        textmod.shadow_text(surface, rank, (cx, top + 52), size=30, color=color, bold=True,
                            anchor="center", shadow=SHADOW)
        textmod.shadow_text(surface, self.info["name"], (card.left + 60, top + 52),
                            size=16, color=COL_SLATE, anchor="midleft", shadow=SHADOW)
        textmod.shadow_text(surface, "x%.2f" % self.info["score"], (card.right - 60, top + 52),
                            size=16, color=COL_TEAL, bold=True, anchor="midright",
                            shadow=SHADOW)
        pygame.draw.line(surface, COL_SAND, (card.left + 48, top + 82), (card.right - 48, top + 82), 2)

        rows = [
            ("营业收入", "%d 星币" % self.score.income, COL_FLAME),
            ("小费", "%d" % self.score.tips, COL_TEAL),
            ("完成订单", "%d 单" % self.score.served, COL_LIME),
            ("跑掉的客人", "%d 单" % self.score.failed, COL_TOMATO),
            ("最高连击", "x%d" % self.score.best_combo, COL_SLATE),
            ("糊菜倒掉", "%d 份" % self.score.burnt_trashed, COL_STEEL),
        ]
        y = top + 118
        for label, value, col in rows:
            textmod.shadow_text(surface, label, (card.left + 60, y), size=19, color=COL_STEEL,
                                anchor="midleft", shadow=SHADOW)
            textmod.shadow_text(surface, value, (card.right - 60, y), size=20, color=col,
                                bold=True, anchor="midright", shadow=SHADOW)
            y += 42

        pygame.draw.line(surface, COL_SAND, (card.left + 48, y - 8), (card.right - 48, y - 8), 2)
        textmod.shadow_text(surface, "净收入", (card.left + 60, y + 28), size=22, color=COL_INK,
                            anchor="midleft", shadow=SHADOW)
        textmod.shadow_text(surface, "★ %d" % self.stars, (card.right - 60, y + 28), size=30,
                            color=COL_GOLD, bold=True, anchor="midright", shadow=SHADOW)
        textmod.shadow_text(surface, "灶币 +%d" % self.coins, (cx, y + 76), size=20,
                            color=COL_TEAL, bold=True, anchor="center", shadow=SHADOW)
        if self.opened:
            textmod.shadow_text(surface, "挑战模式已解锁！同一张桌上再试一次",
                                (cx, card.bottom - 62), size=15, color=COL_FLAME,
                                bold=True, anchor="center", shadow=SHADOW)
        textmod.shadow_text(surface, "Enter 再来一局      Esc 回标题",
                            (cx, card.bottom - 26), size=17, color=COL_SLATE, anchor="center",
                            shadow=SHADOW)
