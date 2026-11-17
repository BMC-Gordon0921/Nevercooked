"""Title card: bright canteen light, one key to start, three ways to cook."""
from __future__ import annotations

import math

import pygame

from core import assets, audio, config, profile, text as textmod
from game.systems import difficulty

COL_IVORY = config.color("ivory")
COL_SAND = config.color("sand")
COL_GLASS = config.color("glass")
COL_TEAL = config.color("teal")
COL_INK = config.color("ink")
COL_STEEL = config.color("steel")
COL_FLAME = config.color("flame_deep")
COL_AMBER = config.color("amber")
COL_CREAM = config.color("cream")
COL_CLAY = config.color("clay")
SHADOW = (66, 52, 38)

CHIP_W, CHIP_H, CHIP_GAP = 196, 78, 18


_WORD_SCALE = 7          # 7x the 12px strike: an 84px wordmark


def _wordmark(parts, scale, *colors, gap=1):
    """The title lockup: pixel glyphs laid out by hand, one flat colour per part.

    No outline and no drop shadow: at 6x a single strike pixel is 6 screen
    pixels, so any offset smears across half a stroke and the glyph turns to
    mud.  Flat colour keeps the pixel grid honest, which is what the font is
    for.
    """
    from core import pixelfont
    glyphs = []
    for part, color in zip(parts, colors):
        for ch in part:
            raw = pixelfont.render(ch, scale, color)
            # Trim the side bearings only: a punctuation glyph is inked in the
            # middle of its cell, so keeping the cell would park the "！" a whole
            # em away from the character before it.  Height stays the cell's so
            # every glyph keeps the same baseline.
            ink = raw.get_bounding_rect()
            if ink.width:
                raw = raw.subsurface(pygame.Rect(ink.x, 0, ink.width, raw.get_height())).copy()
            glyphs.append(raw)
    step = max(0, int(gap)) * scale
    width = sum(g.get_width() for g in glyphs) + step * max(0, len(glyphs) - 1)
    height = max(g.get_height() for g in glyphs)
    out = pygame.Surface((width, height), pygame.SRCALPHA)
    x = 0
    for glyph in glyphs:
        out.blit(glyph, (x, 0))
        x += glyph.get_width() + step
    return out


class TitleScene:
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.data = profile.load()
        self.levels = list(difficulty.ORDER)
        start = getattr(app, "difficulty", difficulty.DEFAULT)
        self.index = self.levels.index(start) if start in self.levels else len(self.levels) // 2
        self.codes = difficulty.codes()
        self.prompt_open = False
        self.buffer = ""
        self.message = ""
        self.message_ok = True
        self.message_t = 0.0
        audio.play_bgm("bgm_canteen_loop", 0.20)

    # -- input ----------------------------------------------------------
    def update(self, dt, intent):
        self.t += dt
        self.message_t = max(0.0, self.message_t - dt)
        if self.prompt_open:
            if intent.menu:
                self.prompt_open = False
                self.buffer = ""
                return
            if intent.backspace:
                self.buffer = self.buffer[:-intent.backspace]
                return
            if intent.text:
                self.buffer = (self.buffer + intent.text)[:24]
                return
            if intent.confirm:
                self._submit_code()
            return
        if intent.code:
            self.prompt_open = True
            self.buffer = ""
            self.message = ""
            return
        if intent.settings:
            from scenes.settings import SettingsScene
            self.app.switch(SettingsScene(self.app, self))
            return
        if intent.nav:
            self.index = (self.index + intent.nav) % len(self.levels)
        if intent.pick and 1 <= intent.pick <= len(self.levels):
            self.index = intent.pick - 1
        level = self.levels[self.index]
        if intent.confirm:
            if not profile.is_unlocked(level, self.data):
                audio.play("sfx_fail", 0.40)
                self.message = "%s 还没解锁：先打个 S，或者按 C 输入兑换码" % difficulty.data(level)["name"]
                self.message_ok = False
                self.message_t = 3.0
                return
            self.app.difficulty = level
            from scenes.game import GameScene
            self.app.switch(GameScene(self.app, level))
        elif intent.menu:
            self.app.running = False

    def _submit_code(self):
        """Redeem one code. Wrong input keeps the prompt open so retyping is cheap."""
        level = difficulty.level_for_code(self.buffer)
        self.prompt_open = False
        self.buffer = ""
        if level is None:
            audio.play("sfx_fail", 0.45)
            self.message = "兑换码无效，再试一次（按 C 重新输入）"
            self.message_ok = False
            self.message_t = 2.6
            return
        self.data, opened = profile.unlock(level, self.data)
        audio.play("sfx_bell", 0.80)
        name = difficulty.data(level)["name"]
        self.message = ("%s 已解锁！按 Enter 开锅" % name) if opened else ("%s 本来就是开着的" % name)
        self.message_ok = True
        self.message_t = 3.2
        if level in self.levels:
            self.index = self.levels.index(level)

    # -- painting -------------------------------------------------------
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
        pygame.draw.line(surface, COL_CLAY, (0, y_top), (config.SCREEN_W, y_top), 2)

    def _chips(self, surface):
        """Difficulty picker. Locked chips stay visible: the player should know
        challenge mode exists before it is open to them."""
        total = len(self.levels) * CHIP_W + (len(self.levels) - 1) * CHIP_GAP
        left = config.SCREEN_W // 2 - total // 2
        top = 458
        for index, level in enumerate(self.levels):
            chip = pygame.Rect(left + index * (CHIP_W + CHIP_GAP), top, CHIP_W, CHIP_H)
            chosen = index == self.index
            open_level = profile.is_unlocked(level, self.data)
            pygame.draw.rect(surface, COL_SAND, chip.move(0, 4), border_radius=10)
            fill = COL_CREAM if open_level else config.color("glass")
            pygame.draw.rect(surface, fill, chip, border_radius=10)
            edge = COL_FLAME if chosen else (COL_CLAY if open_level else COL_STEEL)
            pygame.draw.rect(surface, edge, chip, 3 if chosen else 1, border_radius=10)
            info = difficulty.data(level)
            name_col = COL_INK if open_level else COL_STEEL
            textmod.shadow_text(surface, info["name"], (chip.centerx, chip.y + 22),
                                size=24, color=name_col, bold=True, anchor="center",
                                shadow=(255, 255, 255))
            sub = "结算 x%.2f · 耐心 x%.2f" % (info["score"], info["patience"])
            if not open_level:
                sub = "评 S 解锁，或按 C 兑换"
            textmod.shadow_text(surface, sub, (chip.centerx, chip.y + 50), size=12,
                                color=COL_STEEL if open_level else COL_FLAME,
                                anchor="center", shadow=(255, 255, 255))
            best = profile.best(level, self.data)
            if best:
                textmod.shadow_text(surface, "最佳 ★%d" % best,
                                    (chip.centerx, chip.y + 68), size=11,
                                    color=config.color("teal"), anchor="center",
                                    shadow=(255, 255, 255))

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
        # Wordmark: four characters in fire red, the exclamation in neon teal,
        # drawn one glyph at a time. A single 84px string of a 12px pixel face
        # sets too tight and goes to mush; glyph-by-glyph keeps even air between
        # the letters at any strike size.
        stamp = _wordmark(("欢闹厨房", "！"), _WORD_SCALE, COL_FLAME, COL_TEAL)
        surface.blit(stamp, (cx - stamp.get_width() // 2, 178))
        textmod.shadow_text(surface, "N E V E R C O O K E D !", (cx, 284),
                            size=22, color=COL_STEEL, bold=True, anchor="center",
                            shadow=(255, 255, 255))
        textmod.shadow_text(surface, "碗底港 · 第七码头  ·  三分钟一局", (cx, 320),
                            size=17, color=COL_INK, anchor="center", shadow=(255, 255, 255))

        pulse = int(170 + 70 * math.sin(self.t * 3.0))
        pygame.draw.rect(surface, COL_CREAM, (cx - 150, 372, 300, 62), border_radius=10)
        pygame.draw.rect(surface, COL_CLAY, (cx - 150, 372, 300, 62), 2, border_radius=10)
        textmod.shadow_text(surface, "按 Enter 开始", (cx, 403), size=27,
                            color=(min(240, pulse + 40), min(150, pulse), 40), bold=True,
                            anchor="center", shadow=(255, 255, 255))
        self._chips(surface)
        if config.MAP_ERROR:
            textmod.shadow_text(surface, "地图文件有误，已退回默认厨房：" + config.MAP_ERROR,
                                (cx, config.SCREEN_H - 96), size=13,
                                color=config.color("tomato"), anchor="center",
                                shadow=(255, 255, 255))
        if self.message_t > 0.0:
            textmod.shadow_text(surface, self.message, (cx, 566), size=16,
                                color=COL_TEAL if self.message_ok else COL_FLAME,
                                bold=True, anchor="center", shadow=(255, 255, 255))
        if self.prompt_open:
            self._prompt(surface, cx)
        textmod.shadow_text(surface,
                            "← → 选难度    Tab 设置    F 交互   Q 抛出   C 兑换码",
                            (cx, config.SCREEN_H - 40), size=15, color=COL_INK,
                            anchor="center", shadow=COL_SAND)

    def _prompt(self, surface, cx):
        """Code entry: a small card over a dimmed title, so the picker stays visible."""
        veil = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        veil.fill((12, 18, 28, 160))
        surface.blit(veil, (0, 0))
        card = pygame.Rect(0, 0, 520, 170)
        card.center = (cx, 350)
        pygame.draw.rect(surface, COL_CREAM, card, border_radius=12)
        pygame.draw.rect(surface, COL_CLAY, card, 2, border_radius=12)
        textmod.shadow_text(surface, "输入兑换码", (cx, card.y + 28), size=22,
                            color=COL_INK, bold=True, anchor="center",
                            shadow=(255, 255, 255))
        field = pygame.Rect(card.x + 40, card.y + 50, card.w - 80, 48)
        pygame.draw.rect(surface, (255, 255, 255), field, border_radius=8)
        pygame.draw.rect(surface, COL_TEAL if self.buffer else COL_CLAY, field,
                         2, border_radius=8)
        shown = " ".join(self.buffer)
        if not shown:
            shown = "· · · · · ·"
        elif int(self.t * 2.2) % 2 == 0:
            shown += " ｜"
        textmod.shadow_text(surface, shown, field.center, size=24,
                            color=COL_INK if self.buffer else COL_STEEL,
                            bold=True, anchor="center", shadow=COL_SAND)
        textmod.shadow_text(surface, "Enter 确认   ·   Esc 取消   ·   退格键删除",
                            (cx, card.bottom - 26), size=14, color=COL_STEEL,
                            anchor="center", shadow=(255, 255, 255))
