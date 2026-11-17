"""Settings: how loud the kitchen is, and whether the floor shows the route.

Every change applies the instant it is made -- volume is a live mixer level and
the path toggle only gates a draw call -- so there is no "apply" button and no
way to leave the screen with a change that did not take.  Enter and Esc both
walk back, because a settings screen is not a decision.
"""
from __future__ import annotations

import pygame

from core import audio, config, profile, text as textmod

COL_VOID = config.color("void")
COL_INK = config.color("ink")
COL_SLATE = config.color("slate")
COL_STEEL = config.color("steel")
COL_SILVER = config.color("silver")
COL_FOG = config.color("fog")
COL_CYAN = config.color("cyan")
COL_AMBER = config.color("amber")
COL_WHITE = config.color("white")
COL_TEAL = config.color("teal")

ROWS = (
    ("sfx", "音效音量"),
    ("bgm", "背景音乐"),
    ("path", "地面箭头路径"),
)
class SettingsScene:
    def __init__(self, app, back=None):
        self.app = app
        self.back = back
        self.settings = profile.settings()
        self.index = 0
        self.t = 0.0
        self.message = ""
        self.message_t = 0.0
        audio.set_sfx_volume(self.settings["sfx"])
        audio.set_bgm_volume(self.settings["bgm"])
        audio.play_bgm("bgm_canteen_loop", 0.20)

    # -- data -----------------------------------------------------------
    def _store(self, patch):
        self.settings = profile.save_settings(patch)
        self.message = "已保存"
        self.message_t = 1.4

    def _nudge(self, direction):
        key = ROWS[self.index][0]
        if key == "path":
            self._store({"path": direction > 0})
        else:
            value = max(0.0, min(1.0, round(self.settings[key] + 0.05 * direction, 2)))
            self._store({key: value})
            if key == "sfx":
                audio.set_sfx_volume(value)
                audio.play("sfx_tick", 0.60)
            else:
                audio.set_bgm_volume(value)

    def _leave(self):
        callback = getattr(self.back, "on_resume", None)
        if callable(callback):
            callback()
        if self.back is not None:
            self.app.switch(self.back)
        else:
            from scenes.title import TitleScene
            self.app.switch(TitleScene(self.app))

    # -- loop -----------------------------------------------------------
    def update(self, dt, intent):
        self.t += dt
        self.message_t = max(0.0, self.message_t - dt)
        if intent.menu or intent.confirm:
            self._leave()
            return
        if intent.updown:
            self.index = (self.index + intent.updown) % len(ROWS)
            audio.play("sfx_tick", 0.35)
        if intent.nav:
            self._nudge(intent.nav)
        if intent.pick and 1 <= intent.pick <= len(ROWS):
            self.index = intent.pick - 1

    # -- painting -------------------------------------------------------
    def _sky(self, surface):
        top = COL_VOID
        bottom = config.color("slate")
        bands = 24
        step = config.SCREEN_H // bands
        for index in range(bands):
            f = index / (bands - 1)
            col = tuple(int(top[c] + (bottom[c] - top[c]) * f) for c in range(3))
            pygame.draw.rect(surface, col, (0, index * step, config.SCREEN_W, step + 1))

    def _volume_row(self, surface, rect, value, live):
        segs = 12
        gap = 8
        width = 24
        x = rect.right - segs * (width + gap) + gap
        lit = int(round(value * segs))
        for i in range(segs):
            box = pygame.Rect(x + i * (width + gap), rect.centery - 8, width, 16)
            if i < lit:
                col = COL_CYAN if live else COL_TEAL
                if i >= segs - 3:
                    col = COL_AMBER
                pygame.draw.rect(surface, col, box, border_radius=3)
            else:
                pygame.draw.rect(surface, COL_INK, box, border_radius=3)
                pygame.draw.rect(surface, COL_SLATE, box, 1, border_radius=3)
        textmod.shadow_text(surface, "%d%%" % int(round(value * 100)),
                            (x - 12, rect.centery), size=15, color=COL_SILVER,
                            bold=True, anchor="midright")

    def _toggle(self, surface, rect, on):
        box = pygame.Rect(0, 0, 92, 30)
        box.midright = (rect.right, rect.centery)
        pygame.draw.rect(surface, COL_INK, box, border_radius=15)
        pygame.draw.rect(surface, COL_CYAN if on else COL_STEEL, box, 2, border_radius=15)
        knob = pygame.Rect(0, 0, 24, 24)
        knob.center = (box.x + (box.w - 16 if on else 16), box.centery)
        pygame.draw.rect(surface, COL_CYAN if on else COL_STEEL, knob, border_radius=12)
        # the state word sits on the free side of the pill, never inside the knob
        word_x = box.x + 26 if on else box.right - 26
        textmod.shadow_text(surface, "开" if on else "关", (word_x, box.centery + 1),
                            size=13, color=COL_CYAN if on else COL_SILVER,
                            anchor="center")

    def draw(self, surface):
        self._sky(surface)
        cx = config.SCREEN_W // 2
        card = pygame.Rect(0, 0, 760, 436)
        card.center = (cx, 360)
        shadow = card.move(0, 8)
        veil = pygame.Surface(shadow.size, pygame.SRCALPHA)
        veil.fill((0, 0, 0, 90))
        surface.blit(veil, shadow.topleft)
        pygame.draw.rect(surface, COL_INK, card, border_radius=14)
        pygame.draw.rect(surface, COL_SLATE, card, 2, border_radius=14)

        textmod.shadow_text(surface, "设置", (cx, card.y + 34), size=34,
                            color=COL_WHITE, anchor="center")
        textmod.shadow_text(surface, "改动即时生效，自动保存到 profile.json",
                            (cx, card.y + 62), size=13, color=COL_FOG, anchor="center")

        rows = []
        for i, (key, label) in enumerate(ROWS):
            row = pygame.Rect(card.x + 52, card.y + 104 + i * 78, card.w - 104, 58)
            rows.append(row)
            chosen = i == self.index
            if chosen:
                pygame.draw.rect(surface, COL_CYAN, row.inflate(8, 8), 2, border_radius=10)
                tip = (row.x - 20, row.centery)
                pygame.draw.polygon(surface, COL_CYAN, ((tip[0] - 6, tip[1] - 7),
                                                        (tip[0] - 6, tip[1] + 7),
                                                        (tip[0] + 6, tip[1])))
            textmod.shadow_text(surface, label, (row.x + 8, row.centery - 8), size=19,
                                color=COL_WHITE if chosen else COL_SILVER,
                                anchor="midleft")
            if key == "path":
                on = bool(self.settings["path"])
                sub = "在厨房地面上画出通往下一站的粗箭头"
                textmod.shadow_text(surface, sub, (row.x + 8, row.centery + 14),
                                    size=12, color=COL_FOG, anchor="midleft")
                self._toggle(surface, row, on)
            else:
                value = float(self.settings[key])
                sub = "调低可以只听清设备提示音" if key == "sfx" else "0% 只留音效"
                textmod.shadow_text(surface, sub, (row.x + 8, row.centery + 14),
                                    size=12, color=COL_FOG, anchor="midleft")
                self._volume_row(surface, row, value, chosen)

        hint = "↑↓ 选择    ←→ 调整    Enter / Esc 返回"
        textmod.shadow_text(surface, hint, (cx, card.bottom - 34), size=15,
                            color=COL_FOG, anchor="center")
        if self.message_t > 0 and self.message:
            textmod.shadow_text(surface, self.message, (card.right - 34, card.y + 34),
                                size=13, color=COL_CYAN, bold=True, anchor="midright")
